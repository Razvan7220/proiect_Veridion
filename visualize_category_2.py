import pandas as pd
import filtre as fl

df = pd.read_csv('date_companii.csv')

def debug_candidate_nulls_cat2():
    all_keys = df['input_row_key'].unique()
    
    mapping = {
        'input_main_country_code': 'main_country_code',
        'input_main_postcode': 'main_postcode',
        'input_main_region': 'main_region',
        'input_main_street': 'main_street',
        'input_main_city': 'main_city',
        'input_main_street_number': 'main_street_number'
    }
    
    # Folosim seturi pentru ID-uri unice la nivel de grup
    group_data = {i: {
        'unique_keys': set(), 
        'candidate_entries': [], 
        'input_stats': {k: 0 for k in mapping}, 
        'ver_null_stats': {v: 0 for v in mapping.values()}
    } for i in range(1, 7)}
    
    print(f"[*] Analyzing Category [2] (Unique Companies vs Candidates)...")

    for key in all_keys:
        variants = df[df['input_row_key'] == key].reset_index(drop=True)
        input_row = variants.iloc[0]
        
        res_list = {v: fl.filtru_tara(input_row, variants) if v == 'main_country_code' else 
                       fl.filtru_cod_postal(input_row, variants) if v == 'main_postcode' else
                       fl.filtru_regiune(input_row, variants) if v == 'main_region' else
                       fl.filtru_strada(input_row, variants) if v == 'main_street' else
                       fl.filtru_oras(input_row, variants) if v == 'main_city' else
                       fl.filtru_numar_strada(input_row, variants) for v in mapping.values()}
        
        res_name = fl.filtru_nume_flexibil(input_row, variants, threshold=0.1)

        best_cat = 5
        cat2_variants = []

        for i in range(len(variants)):
            loc_score = sum([i in matches for matches in res_list.values()])
            name_match = i in res_name
            if name_match and loc_score >= 2: curr = 1
            elif name_match and loc_score == 1: curr = 2
            elif loc_score >= 1: curr = 3
            else: curr = 5
            if curr < best_cat: best_cat = curr
            if curr == 2: cat2_variants.append(i)

        if best_cat == 2:
            populated_input_cols = [k for k in mapping if pd.notnull(input_row.get(k)) and str(input_row.get(k)).lower() != 'nan' and str(input_row.get(k)).strip() != '']
            n = len(populated_input_cols)
            
            if n > 0:
                group_data[n]['unique_keys'].add(key)
                for idx in cat2_variants:
                    cand_row = variants.iloc[idx]
                    
                    # Stocăm intrarea candidatului
                    group_data[n]['candidate_entries'].append({
                        'key': key,
                        'veridion_nulls': [v for k, v in mapping.items() if k in populated_input_cols and (pd.isnull(cand_row.get(v)) or str(cand_row.get(v)).lower() == 'nan')]
                    })
                    
                    # Statistici agregate per atribut (la nivel de candidați)
                    for inp_col in populated_input_cols:
                        ver_col = mapping[inp_col]
                        group_data[n]['input_stats'][inp_col] += 1
                        if pd.isnull(cand_row.get(ver_col)) or str(cand_row.get(ver_col)).lower() == 'nan':
                            group_data[n]['ver_null_stats'][ver_col] += 1

    while True:
        print("\n" + "="*85)
        print(" CATEGORY [2] DEBUGGER (Unique Companies)")
        print("="*85)
        total_unique_sum = 0
        for i in sorted(group_data.keys(), reverse=True):
            unique_count = len(group_data[i]['unique_keys'])
            cand_count = len(group_data[i]['candidate_entries'])
            if unique_count > 0:
                total_unique_sum += unique_count
                print(f" [{i}] {i}/6 Input fields: {unique_count:>3} firms ({cand_count:>3} candidates)")
        print("-" * 85)
        print(f" TOTAL UNIQUE FIRMS IN CATEGORY [2]: {total_unique_sum}")
        
        cmd = input("\nSelect group [1-6] or [q] Quit: ").lower().strip()
        if cmd == 'q': break
        
        if cmd.isdigit() and int(cmd) in range(1, 7):
            n = int(cmd)
            group = group_data[n]
            total_cands = len(group['candidate_entries'])
            
            if total_cands == 0:
                print("[!] No data.")
                continue

            print(f"\n" + "░"*20 + f" STATS FOR GROUP {n}/6 ({total_cands} candidates) " + "░"*20)
            print(f"{'Input Attribute':<30} | {'Input Pres.':<12} | {'Veridion NULLs'}")
            print("-" * 85)
            
            for inp_col, ver_col in mapping.items():
                in_count = group['input_stats'][inp_col]
                vn_count = group['ver_null_stats'][ver_col]
                vn_perc = (vn_count / in_count) * 100 if in_count > 0 else 0
                
                print(f" -> {inp_col:<27}: {in_count:>3} candidates | {vn_count:>3} ({vn_perc:>5.1f}%) are NULL")
            
            print(f"\nUnique IDs in this group: {', '.join(map(str, sorted(list(group['unique_keys']))))}")
        else:
            print("[!] Invalid selection.")

if __name__ == "__main__":
    debug_candidate_nulls_cat2()