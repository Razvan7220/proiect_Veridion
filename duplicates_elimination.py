import pandas as pd
import os
from strategy_category_1 import resolve_category_1
from strategy_category_2 import resolve_category_2
from strategy_category_3 import resolve_category_3

def generate_final_poc_dataset():
    # 1. Setup output directory
    output_dir = 'results'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 2. Run all strategies
    res1 = resolve_category_1()
    res2 = resolve_category_2()
    res3 = resolve_category_3()

    df_all_strategies = pd.concat([res1, res2, res3], ignore_index=True)

    # 3. FILE 1: RESOLVED (The winners)
    resolved_statuses = ['Certain', 'Resolved by Context/Rank', 'Resolved by Deep Context']
    df_resolved = df_all_strategies[df_all_strategies['status'].isin(resolved_statuses)]
    
    resolved_path = os.path.join(output_dir, 'resolved_entities.csv')
    df_resolved[['key', 'vid']].to_csv(resolved_path, index=False)

    # 4. --- LOGICA PENTRU DUPLICATE (Ce ai întrebat) ---
    # Căutăm Veridion ID-urile care apar de mai multe ori în rezultatele rezolvate
    df_duplicates = df_resolved[df_resolved.duplicated(subset=['vid'], keep=False)].sort_values('vid')
    
    duplicates_path = os.path.join(output_dir, 'internal_duplicates.csv')
    df_duplicates[['key', 'vid']].to_csv(duplicates_path, index=False)

    # 5. FILE 2: AMBIGUOUS (Ties)
    df_ties = df_all_strategies[df_all_strategies['status'] == 'Absolute Tie']
    ties_path = os.path.join(output_dir, 'ambiguous_ties.csv')
    df_ties[['key']].to_csv(ties_path, index=False)

    # 6. FILE 3: REJECTED (Mismatches)
    df_search = pd.read_csv('date_companii.csv')
    all_keys_with_variants = set(df_search['input_row_key'].unique())
    processed_keys = set(df_all_strategies['key'].unique())
    
    rejected_keys = all_keys_with_variants - processed_keys
    df_rejected = pd.DataFrame({'key': list(rejected_keys)})
    rejected_path = os.path.join(output_dir, 'rejected_mismatches.csv')
    df_rejected.to_csv(rejected_path, index=False)

    # 7. Summary Printing
    print(f"\n" + "="*50)
    print(f" POC DISTRIBUTION SUMMARY")
    print(f"="*50)
    print(f" -> [✓] Resolved Entities:   {len(df_resolved):>4}")
    print(f" -> [D] Internal Duplicates: {len(df_duplicates):>4} (Multiple keys -> same VID)")
    print(f" -> [?] Ambiguous Ties:      {len(df_ties):>4}")
    print(f" -> [!] Hard Mismatches/Risk: {len(df_rejected):>4}")
    print(f"="*50)

if __name__ == "__main__":
    generate_final_poc_dataset()