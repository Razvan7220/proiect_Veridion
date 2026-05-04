import pandas as pd
import filtre as fl
import numpy as np

# Load the data
df = pd.read_csv('date_companii.csv')

def get_deep_context_score(input_name, candidate_row):
    input_tokens = fl.tokenize(input_name)
    cand_name_tokens = fl.tokenize(candidate_row['company_name'])
    missing_words = input_tokens - cand_name_tokens
    if not missing_words: return 0
    
    search_fields = [
        'generated_description', 'short_description', 'long_description',
        'generated_business_tags', 'business_tags', 
        'main_industry', 'main_sector', 'naics_2022_primary_label'
    ]
    full_context = " ".join([str(candidate_row.get(f, '')) for f in search_fields]).lower()
    found_count = sum(1 for word in missing_words if word in full_context)
    return found_count / len(missing_words)

def get_completeness_score(row):
    rich_fields = ['revenue', 'employee_count', 'primary_email', 'primary_phone', 'year_founded', 'main_business_category']
    score = sum(1 for field in rich_fields if pd.notnull(row.get(field)) and str(row.get(field)).lower() != 'nan')
    return score / len(rich_fields)

def resolve_category_3():
    all_keys = df['input_row_key'].unique()
    func_map = {
        'main_country_code': fl.filtru_tara, 'main_postcode': fl.filtru_cod_postal,
        'main_region': fl.filtru_regiune, 'main_street': fl.filtru_strada,
        'main_city': fl.filtru_oras, 'main_street_number': fl.filtru_numar_strada
    }
    mapping_input_to_ver = {
        'input_main_country_code': 'main_country_code', 'input_main_postcode': 'main_postcode',
        'input_main_region': 'main_region', 'input_main_street': 'main_street',
        'input_main_city': 'main_city', 'input_main_street_number': 'main_street_number'
    }

    cat3_keys = []
    hard_mismatch_keys = set()
    clean_keys = set()

    # --- PHASE 1: RISK ASSESSMENT ---
    for key in all_keys:
        variants = df[df['input_row_key'] == key].reset_index(drop=True)
        input_row = variants.iloc[0]
        res_list = {col: func(input_row, variants) for col, func in func_map.items()}
        res_raw_loc = fl.filtru_locations_brut(input_row, variants)
        res_name_flex = fl.filtru_nume_flexibil(input_row, variants, threshold=0.1)

        best_cat = 5
        cat3_indices = []

        for i in range(len(variants)):
            loc_score = sum([i in matches for matches in res_list.values()]) + (1 if i in res_raw_loc else 0)
            name_match = i in res_name_flex
            
            if name_match and loc_score >= 2: curr = 1
            elif name_match and loc_score == 1: curr = 2
            elif loc_score >= 1: curr = 3
            else: curr = 5
            
            if curr < best_cat: best_cat = curr
            if curr == 3: cat3_indices.append(i)

        if best_cat == 3:
            cat3_keys.append(key)
            has_hard_mismatch = False
            for idx in cat3_indices:
                cand_row = variants.iloc[idx]
                for inp_col, ver_col in mapping_input_to_ver.items():
                    v_in, v_ver = input_row.get(inp_col), cand_row.get(ver_col)
                    if pd.notnull(v_in) and str(v_in).strip() != '' and pd.notnull(v_ver) and str(v_ver).strip() != '' and str(v_ver).lower() != 'nan':
                        if idx not in res_list[ver_col]:
                            has_hard_mismatch = True; break
            
            if has_hard_mismatch: hard_mismatch_keys.add(key)
            else: clean_keys.add(key)

    # --- PRINT STATS ---
    print("\n" + "="*75)
    print(" CATEGORY [3] RISK ASSESSMENT: HARD MISMATCH VS CLEAN GAPS")
    print("="*75)
    print(f" TOTAL COMPANIES IN CATEGORY [3]          :  {len(cat3_keys):>4}")
    print("-" * 75)
    print(f" [!] HARD MISMATCHES (Conflicting Loc)    :  {len(hard_mismatch_keys):>4}")
    print(f" [✓] CLEAN / NULL GAPS (No Conflict)      :  {len(clean_keys):>4}")
    print("="*75)

    # --- PHASE 2: RESOLUTION ---
    final_results = []
    for key in clean_keys:
        variants = df[df['input_row_key'] == key].reset_index(drop=True)
        input_row = variants.iloc[0]; input_name = input_row['input_company_name']
        res_list = {col: func(input_row, variants) for col, func in func_map.items()}
        res_raw_loc = fl.filtru_locations_brut(input_row, variants)
        res_name_flex = fl.filtru_nume_flexibil(input_row, variants, threshold=0.1)

        qualified = []
        for i, row in variants.iterrows():
            loc_score = sum([i in matches for matches in res_list.values()]) + (1 if i in res_raw_loc else 0)
            if loc_score >= 1 and i not in res_name_flex:
                ctx_score = get_deep_context_score(input_name, row)
                # Scor calculat pentru rank
                current_rank = (loc_score * 5) + (ctx_score * 20)

                qualified.append({
                    "id": i, "loc": loc_score, "ctx": ctx_score, 
                    "vid": row['veridion_id'], "v_name": row['company_name'],
                    "rank": current_rank
                })

        if qualified:
            # Sortăm după Rank
            qualified.sort(key=lambda x: x['rank'], reverse=True)
            
            best = qualified[0]
            
            # --- LOGICA DE TIE-BREAKER ADĂUGATĂ ---
            if len(qualified) > 1:
                second = qualified[1]
                if best['rank'] == second['rank']:
                    status = "Absolute Tie"
                else:
                    status = "Resolved by Deep Context" if best['ctx'] > 0 else "Location Match Only (Weak)"
            else:
                status = "Resolved by Deep Context" if best['ctx'] > 0 else "Location Match Only (Weak)"
            # --------------------------------------

            final_results.append({
                "key": int(key), 
                "status": status, 
                "ctx": round(best['ctx'], 2),
                "loc": best['loc'], 
                "vid": best['vid'], 
                "v_name": best['v_name'],
                "rank": best['rank']
            })

    res_df = pd.DataFrame(final_results)
    if not res_df.empty:
        print("\n=== RESOLUTION SUMMARY (CLEAN CAT 3) ===")
        print(res_df.sort_values('ctx', ascending=False)[['key', 'status', 'ctx', 'loc', 'v_name']].to_string(index=False))
    
    return res_df

if __name__ == "__main__":
    resolve_category_3()