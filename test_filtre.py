import pandas as pd
import filtre as fl

df = pd.read_csv('date_companii.csv')

def run_filter_test(row_key):
    variants = df[df['input_row_key'] == row_key].reset_index(drop=True)
    
    if variants.empty:
        print(f"[-] No data found for key: {row_key}")
        return

    input_row = variants.iloc[0]
    
    print("="*100)
    print(f"FILTER TESTING FOR: {input_row['input_company_name']} (Key: {row_key})")
    print(f"Input Data: {input_row['input_main_country_code']}, {input_row['input_main_postcode']}, {input_row['input_main_street']}")
    print("="*100)

    results = {
        "Country": fl.filtru_tara(input_row, variants),
        "Postcode": fl.filtru_cod_postal(input_row, variants),
        "Region": fl.filtru_regiune(input_row, variants),
        "Street": fl.filtru_strada(input_row, variants),
        "Name": fl.filtru_nume(input_row, variants)
    }

    print(f"{'FILTER':<15} | {'PASSED IDs':<30} | {'STATUS'}")
    print("-" * 100)
    
    for filter_name, ids in results.items():
        status = "PASSED" if len(ids) > 0 else "EMPTY (Blocked all)"
        ids_str = str(ids) if ids else "None"
        print(f"{filter_name:<15} | {ids_str:<30} | {status}")
    
    print("\n")

if __name__ == "__main__":
    for k in [0, 1, 2]:
        run_filter_test(k)