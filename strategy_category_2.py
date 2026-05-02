import pandas as pd
import filtre as fl
import numpy as np

# Load the data
df = pd.read_csv('date_companii.csv')

def extract_numbers_local(val):
    if pd.isna(val): return ""
    return "".join(filter(str.isdigit, str(val)))

def run_recovery_analysis():
    all_keys = df['input_row_key'].unique()
    total_companies = len(all_keys)
    
    # Tracking for Category [2]
    cat2_keys = []
    recovered_keys = []
    recovery_reasons = {"city_found": 0, "pc_found": 0, "both_found": 0}

    print(f"[*] Starting Recovery Analysis for Category [2] using 'locations' field...")

    for key in all_keys:
        variants = df[df['input_row_key'] == key].reset_index(drop=True)
        input_row = variants.iloc[0]
        
        # Standard filters
        res_country = fl.filtru_tara(input_row, variants)
        res_pc      = fl.filtru_cod_postal(input_row, variants)
        res_region  = fl.filtru_regiune(input_row, variants)
        res_street  = fl.filtru_strada(input_row, variants)
        res_city    = fl.filtru_oras(input_row, variants)
        res_number  = fl.filtru_numar_strada(input_row, variants)
        res_name    = fl.filtru_nume_flexibil(input_row, variants, threshold=0.1)

        best_cat = 5
        cat2_indices = []

        for i in range(len(variants)):
            # Standard loc_score (Structured fields only)
            loc_score = sum([
                i in res_country, i in res_pc, i in res_region, 
                i in res_street, i in res_city, i in res_number
            ])
            name_match = i in res_name

            if name_match and loc_score >= 2: curr = 1
            elif name_match and loc_score == 1: curr = 2
            elif loc_score >= 1: curr = 3
            else: curr = 5
            
            if curr < best_cat: best_cat = curr
            if curr == 2: cat2_indices.append(i)

        # If it's a Category [2] company, we try to "Recover" it
        if best_cat == 2:
            cat2_keys.append(key)
            is_recovered = False
            
            input_city = str(input_row.get('input_main_city', '')).lower().strip()
            input_pc = extract_numbers_local(input_row.get('input_main_postcode', ''))

            for idx in cat2_indices:
                raw_locations = str(variants.iloc[idx].get('locations', '')).lower()
                
                city_in_raw = input_city != '' and input_city in raw_locations
                pc_in_raw = input_pc != '' and input_pc in extract_numbers_local(raw_locations)

                if city_in_raw or pc_in_raw:
                    if not is_recovered:
                        recovered_keys.append(key)
                        is_recovered = True
                    
                    # Update reasons (for statistics)
                    if city_in_raw and pc_in_raw: recovery_reasons["both_found"] += 1
                    elif city_in_raw: recovery_reasons["city_found"] += 1
                    elif pc_in_raw: recovery_reasons["pc_found"] += 1
                    break

    # --- FINAL STATISTICS ---
    cat2_count = len(cat2_keys)
    rec_count = len(recovered_keys)
    remaining = cat2_count - rec_count

    print("\n" + "="*65)
    print(" RECOVERY ANALYSIS RESULTS (Category [2] -> [1])")
    print("="*65)
    print(f" Initial Category [2] Companies : {cat2_count:>5}")
    print(f" Recovered (Moved to Cat [1])    : {rec_count:>5} ({ (rec_count/cat2_count)*100 if cat2_count > 0 else 0:>5.1f}%)")
    print(f" Remaining in Category [2]       : {remaining:>5}")
    print("-" * 65)
    print(" RECOVERY REASONS (How they were saved):")
    print(f" -> Found City in 'locations'    : {recovery_reasons['city_found']:>5}")
    print(f" -> Found Postcode in 'locations': {recovery_reasons['pc_found']:>5}")
    print(f" -> Found Both in 'locations'    : {recovery_reasons['both_found']:>5}")
    print("="*65)

    if recovered_keys:
        show_ids = input("\nShow Recovered IDs? (y/n): ").lower().strip()
        if show_ids == 'y':
            print(f"Recovered IDs: {', '.join(map(str, recovered_keys))}")

if __name__ == "__main__":
    run_recovery_analysis()