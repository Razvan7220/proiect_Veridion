import pandas as pd
import filtre as fl
from strategy_category_1 import get_deep_context_score, get_completeness_score

# Load the dataset
df = pd.read_csv('date_companii.csv')

def debug_key_resolution(row_key):
    """
    Detailed breakdown of the scoring mechanism for a specific input key.
    Shows LOC, CTX, NAM, and COM scores contributing to the final RANK.
    """
    variants = df[df['input_row_key'] == row_key].reset_index(drop=True)
    if variants.empty:
        print(f"[-] Key {row_key} not found.")
        return

    input_row = variants.iloc[0]
    input_name = input_row['input_company_name']
    input_tokens = fl.tokenize(input_name)

    print("="*100)
    print(f"DEBUGGING KEY: {row_key} | INPUT: '{input_name}'")
    print(f"INPUT TOKENS: {input_tokens}")
    print("="*100)

    # Execute base filters
    res_country = fl.filtru_tara(input_row, variants)
    res_pc      = fl.filtru_cod_postal(input_row, variants)
    res_region  = fl.filtru_regiune(input_row, variants)
    res_street  = fl.filtru_strada(input_row, variants)
    res_name_flex = fl.filtru_nume_flexibil(input_row, variants, threshold=0.5)

    results = []
    for i, row in variants.iterrows():
        # Calculate individual metrics
        loc_score = sum([i in res_country, i in res_pc, i in res_region, i in res_street])
        
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

    # Table Header
    header = f"{'ID':<3} | {'COMPANY NAME':<40} | {'LOC':<3} | {'CTX':<4} | {'NAM':<4} | {'COM':<4} | {'RANK':<6} | {'STATUS'}"
    print(header)
    print("-" * len(header))
    
    for r in results:
        status = "[OK]" if r['QUAL'] else "[FAIL]"
        print(f"{r['ID']:<3} | {r['Name']:<40} | {r['LOC']:<3} | {r['CTX']:<4} | {r['NAM']:<4} | {r['COM']:<4} | {r['RANK']:<6} | {status}")

if __name__ == "__main__":
    # Change the ID here to debug different problematic keys
    target_key = 170 
    debug_key_resolution(target_key)