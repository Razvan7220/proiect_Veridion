import pandas as pd
import filtre as fl
import numpy as np

# Load the data
df = pd.read_csv('date_companii.csv')

def get_deep_context_score(input_name, candidate_row):
    """Searches for missing input words across descriptions, tags, and industry labels."""
    input_tokens = fl.tokenize(input_name)
    cand_name_tokens = fl.tokenize(candidate_row['company_name'])
    missing_words = input_tokens - cand_name_tokens
    if not missing_words:
        return 0
    search_fields = [
        'generated_description', 'short_description', 'long_description',
        'generated_business_tags', 'business_tags', 
        'main_industry', 'main_sector', 'naics_2022_primary_label'
    ]
    full_context = " ".join([str(candidate_row.get(f, '')) for f in search_fields]).lower()
    found_count = sum(1 for word in missing_words if word in full_context)
    return found_count / len(missing_words)

def get_completeness_score(row):
    """Measures profile richness (revenue, employees, contact info) as a final tie-breaker."""
    rich_fields = [
        'revenue', 'employee_count', 'primary_email', 
        'primary_phone', 'year_founded', 'main_business_category'
    ]
    score = sum(1 for field in rich_fields if pd.notnull(row.get(field)) and str(row.get(field)).lower() != 'nan')
    return score / len(rich_fields)

def run_strategy_category_2():
    all_keys = df['input_row_key'].unique()
    
    func_map = {
        'main_country_code': fl.filtru_tara,
        'main_postcode': fl.filtru_cod_postal,
        'main_region': fl.filtru_regiune,
        'main_street': fl.filtru_strada,
        'main_city': fl.filtru_oras,
        'main_street_number': fl.filtru_numar_strada
    }
    
    mapping_input_to_ver = {
        'input_main_country_code': 'main_country_code',
        'input_main_postcode': 'main_postcode',
        'input_main_region': 'main_region',
        'input_main_street': 'main_street',
        'input_main_city': 'main_city',
        'input_main_street_number': 'main_street_number'
    }

    cat2_firms = []
    hard_mismatch_keys = set()
    only_null_gaps_keys = set()

    print(f"[*] Scanning Category [2] firms for Hard Mismatches...")

    # --- PHASE 1: RISK ASSESSMENT ---
    for key in all_keys:
        variants = df[df['input_row_key'] == key].reset_index(drop=True)
        input_row = variants.iloc[0]
        
        res_list = {col: func(input_row, variants) for col, func in func_map.items()}
        res_raw_loc = fl.filtru_locations_brut(input_row, variants)
        res_name = fl.filtru_nume_flexibil(input_row, variants, threshold=0.1)

        best_cat = 5
        cat2_indices = []

        for i in range(len(variants)):
            loc_score = sum([i in matches for matches in res_list.values()]) + (1 if i in res_raw_loc else 0)
            name_match = i in res_name
            
            if name_match and loc_score >= 2: curr = 1
            elif name_match and loc_score == 1: curr = 2
            elif loc_score >= 1: curr = 3
            else: curr = 5
            
            if curr < best_cat: best_cat = curr
            if curr == 2: cat2_indices.append(i)

        if best_cat == 2:
            cat2_firms.append(key)
            has_hard_mismatch = False
            
            for idx in cat2_indices:
                cand_row = variants.iloc[idx]
                for inp_col, ver_col in mapping_input_to_ver.items():
                    val_in = input_row.get(inp_col)
                    val_ver = cand_row.get(ver_col)
                    
                    if pd.notnull(val_in) and str(val_in).strip() != '' and \
                       pd.notnull(val_ver) and str(val_ver).strip() != '' and \
                       str(val_ver).lower() != 'nan':
                        
                        if idx not in res_list[ver_col]:
                            has_hard_mismatch = True
                            break
            
            if has_hard_mismatch:
                hard_mismatch_keys.add(key)
            else:
                only_null_gaps_keys.add(key)

    # Convert ID lists
    mismatch_ids = sorted([int(x) for x in hard_mismatch_keys])
    null_ids = sorted([int(x) for x in only_null_gaps_keys])

    # Output Part 1
    print("\n" + "="*75)
    print(" CATEGORY [2] RISK ASSESSMENT: HARD MISMATCH VS NULL GAPS")
    print("="*75)
    print(f" TOTAL COMPANIES IN CATEGORY [2]          :  {len(cat2_firms):>4}")
    print("-" * 75)
    print(f" [!] HARD MISMATCHES (Conflicting)    :  {len(mismatch_ids):>4} ({ (len(mismatch_ids)/len(cat2_firms))*100:>5.1f}%)")
    print(f" [✓] ONLY NULL GAPS (Missing Data)    :  {len(null_ids):>4} ({ (len(null_ids)/len(cat2_firms))*100:>5.1f}%)")
    print("="*75)

    print(f"\n[!] HARD MISMATCH IDs ({len(mismatch_ids)}):")
    print(f"{', '.join(map(str, mismatch_ids))}")
    
    print(f"\n[✓] ONLY NULL GAPS IDs ({len(null_ids)}):")
    print(f"{', '.join(map(str, null_ids))}")
    print("-" * 75)

    # --- PHASE 2: RESOLUTION FOR NULL GAPS ---
    print(f"\n[*] Resolving the null gaps companies using Name & Context logic...")
    
    final_results = []

    for key in only_null_gaps_keys:
        variants = df[df['input_row_key'] == key].reset_index(drop=True)
        input_row = variants.iloc[0]
        input_name = input_row['input_company_name']
        
        # Re-apply filters for scoring
        res_country = fl.filtru_tara(input_row, variants)
        res_pc      = fl.filtru_cod_postal(input_row, variants)
        res_region  = fl.filtru_regiune(input_row, variants)
        res_street  = fl.filtru_strada(input_row, variants)
        res_city    = fl.filtru_oras(input_row, variants)
        res_number  = fl.filtru_numar_strada(input_row, variants)
        res_raw_loc = fl.filtru_locations_brut(input_row, variants)
        res_name_flex = fl.filtru_nume_flexibil(input_row, variants, threshold=0.1)

        qualified = []
        for i, row in variants.iterrows():
            loc_score = sum([i in res_country, i in res_pc, i in res_region, i in res_street, i in res_city, i in res_number, i in res_raw_loc])
            
            # Criteriu: Trebuie să fie varianta de Cat 2 a firmei (Name Match + 1 Loc)
            if i in res_name_flex and loc_score == 1:
                input_tokens = fl.tokenize(input_name)
                cand_tokens = fl.tokenize(row['company_name'])
                name_score = len(input_tokens.intersection(cand_tokens)) / len(input_tokens) if input_tokens else 0
                
                context_score = get_deep_context_score(input_name, row)
                comp_score = get_completeness_score(row)

                qualified.append({
                    "id": i,
                    "loc_score": loc_score,
                    "name_score": name_score,
                    "context_score": context_score,
                    "comp_score": comp_score,
                    "total_rank": (loc_score * 10) + (context_score * 5) + (name_score * 2) + comp_score,
                    "vid": row['veridion_id'],
                    "name_match": row['company_name']
                })

        if qualified:
            # Hierarchical Sort exact ca la Cat 1
            qualified.sort(key=lambda x: (x['loc_score'], x['context_score'], x['name_score'], x['comp_score']), reverse=True)
            
            best = qualified[0]
            if len(qualified) == 1:
                status = "Certain"
            else:
                second = qualified[1]
                if best['total_rank'] > second['total_rank']:
                    status = "Resolved by Context/Rank"
                else:
                    status = "Absolute Tie"

            final_results.append({
                "key": int(key), "status": status, "best_id": best['id'],
                "loc": best['loc_score'], "name": round(best['name_score'], 2),
                "context": round(best['context_score'], 2), "rank": round(best['total_rank'], 2),
                "vid": best['vid'], "name_match": best['name_match']
            })

    res_df = pd.DataFrame(final_results)
    if not res_df.empty:
        print("\n=== RESOLUTION SUMMARY (NULL GAPS) ===")
        print(res_df['status'].value_counts().to_string())
        print("-" * 75)
        # Sortăm după key pentru un tabel ordonat
       # print(res_df.sort_values('key')[['key', 'status', 'name', 'rank', 'name_match']].to_string(index=False))
    else:
        print("No Null Gap companies could be resolved.")

if __name__ == "__main__":
    run_strategy_category_2()