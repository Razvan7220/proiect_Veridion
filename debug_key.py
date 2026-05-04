import pandas as pd
import filtre as fl
from strategy_category_1 import get_deep_context_score, get_completeness_score

# Load the dataset
df = pd.read_csv('date_companii.csv')

def debug_key_resolution(row_key):
    """
    Detailed breakdown of the scoring mechanism for a specific input key.
    Reflects the updated 7-point Location Score.
    """
    variants = df[df['input_row_key'] == row_key].reset_index(drop=True)
    if variants.empty:
        print(f"[-] Key {row_key} not found.")
        return

    input_row = variants.iloc[0]
    input_name = input_row['input_company_name']
    input_tokens = fl.tokenize(input_name)

    print("="*110)
    print(f"DEBUGGING KEY: {row_key} | INPUT: '{input_name}'")
    print(f"INPUT TOKENS: {input_tokens}")
    print("="*110)

    # 1. Execute all 7 location filters
    res_country = fl.filtru_tara(input_row, variants)
    res_pc      = fl.filtru_cod_postal(input_row, variants)
    res_region  = fl.filtru_regiune(input_row, variants)
    res_street  = fl.filtru_strada(input_row, variants)
    res_city    = fl.filtru_oras(input_row, variants)
    res_number  = fl.filtru_numar_strada(input_row, variants)
    res_raw_loc = fl.filtru_locations_brut(input_row, variants)
    
    # 2. Execute name filter (using 0.1 threshold to match current strategy)
    res_name_flex = fl.filtru_nume_flexibil(input_row, variants, threshold=0.1)

    results = []
    for i, row in variants.iterrows():
        # Calculate LOC score based on all 7 indicators
        loc_score = sum([
            i in res_country, 
            i in res_pc, 
            i in res_region, 
            i in res_street,
            i in res_city,
            i in res_number,
            i in res_raw_loc
        ])
        
        cand_tokens = fl.tokenize(row['company_name'])
        common = input_tokens.intersection(cand_tokens)
        name_score = len(common) / len(input_tokens) if input_tokens else 0
        
        context_score = get_deep_context_score(input_name, row)
        comp_score = get_completeness_score(row)
        
        # Scoring Formula: Location (10x) > Context (5x) > Name (2x) > Completeness (1x)
        total_rank = (loc_score * 10) + (context_score * 5) + (name_score * 2) + comp_score

        results.append({
            "ID": i,
            "Name": str(row['company_name'])[:40],
            "LOC": loc_score,
            "CTX": round(context_score, 2),
            "NAM": round(name_score, 2),
            "COM": round(comp_score, 2),
            "RANK": round(total_rank, 2),
            "QUAL": (i in res_name_flex and loc_score >= 2)
        })

    # Sort candidates by Rank descending
    results.sort(key=lambda x: x['RANK'], reverse=True)

    # Table Header (Extended for 110 chars width)
    header = f"{'ID':<3} | {'COMPANY NAME':<40} | {'LOC':<3} | {'CTX':<4} | {'NAM':<4} | {'COM':<4} | {'RANK':<6} | {'STATUS'}"
    print(header)
    print("-" * len(header))
    
    for r in results:
        # Status shows [OK] if it meets Category 1 criteria (Name match + Loc >= 2)
        status = "[OK]" if r['QUAL'] else "[FAIL]"
        print(f"{r['ID']:<3} | {r['Name']:<40} | {r['LOC']:<3} | {r['CTX']:<4} | {r['NAM']:<4} | {r['COM']:<4} | {r['RANK']:<6} | {status}")

if __name__ == "__main__":
    # Target keys with ties to see how they rank now
    target_key = 66
    debug_key_resolution(target_key)