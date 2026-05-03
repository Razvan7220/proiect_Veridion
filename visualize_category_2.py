import pandas as pd
import filtre as fl
import numpy as np

df = pd.read_csv('date_companii.csv')

def analyze_cat2_risk_summary():
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

    total = len(cat2_firms)
    mismatch_count = len(hard_mismatch_keys)
    null_count = len(only_null_gaps_keys)

    # Convertim ID-urile in Python int pentru a elimina np.int64 si le sortam
    mismatch_ids = sorted([int(x) for x in hard_mismatch_keys])
    null_ids = sorted([int(x) for x in only_null_gaps_keys])

    print("\n" + "="*75)
    print(" CATEGORY [2] RISK ASSESSMENT: HARD MISMATCH VS NULL GAPS")
    print("="*75)
    print(f" TOTAL COMPANIES IN CATEGORY [2]          :  {total:>4}")
    print("-" * 75)
    print(f" [!] HARD MISMATCHES (Conflicting)    :  {mismatch_count:>4} ({ (mismatch_count/total)*100:>5.1f}%)")
    print(f" [✓] ONLY NULL GAPS (Missing Data)    :  {null_count:>4} ({ (null_count/total)*100:>5.1f}%)")
    print("="*75)

    print(f"\n[!] HARD MISMATCH IDs ({mismatch_count}):")
    print(f"{', '.join(map(str, mismatch_ids))}")
    
    print(f"\n[✓] ONLY NULL GAPS IDs ({null_count}):")
    print(f"{', '.join(map(str, null_ids))}")
    print("-" * 75)

if __name__ == "__main__":
    analyze_cat2_risk_summary()