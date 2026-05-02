import pandas as pd
import filtre as fl 

# Load the data
df = pd.read_csv('date_companii.csv')

def run_interactive_stats():
    all_keys = df['input_row_key'].unique()
    total_companies = len(all_keys)
    
    # Category Mapping - Inverted [2] and [3]
    category_map = {
        1: "Match 90% (2+ Locations + Name)",
        2: "Name + 1 Location (Possible Match)",          # Acum pe pozitia 2
        3: "Location Found (1+), but NO Name Match",     # Acum pe pozitia 3
        4: "Name Only (Zero Location - RISK)",
        5: "No Match Found"
    }

    stats = {cat: 0 for cat in category_map.values()}
    distribution = {cat: {} for cat in category_map.values()}

    print(f"[*] Analyzing {total_companies} companies. Please wait...")

    for key in all_keys:
        variants = df[df['input_row_key'] == key].reset_index(drop=True)
        input_row = variants.iloc[0]
        
        res_country = fl.filtru_tara(input_row, variants)
        res_pc      = fl.filtru_cod_postal(input_row, variants)
        res_region  = fl.filtru_regiune(input_row, variants)
        res_street  = fl.filtru_strada(input_row, variants)
        res_name    = fl.filtru_nume_flexibil(input_row, variants, threshold=0.1)

        counts_in_group = {cat: 0 for cat in category_map.values()}

        for i in range(len(variants)):
            loc_score = sum([i in res_country, i in res_pc, i in res_region, i in res_street])
            name_match = i in res_name

            if name_match and loc_score >= 2:
                counts_in_group[category_map[1]] += 1
            elif name_match and loc_score == 1:
                counts_in_group[category_map[2]] += 1
            elif loc_score >= 1:
                counts_in_group[category_map[3]] += 1
            elif name_match and loc_score == 0:
                counts_in_group[category_map[4]] += 1
            else:
                counts_in_group[category_map[5]] += 1

        found_cat = None
        for i in range(1, 6):
            cat_name = category_map[i]
            if counts_in_group[cat_name] > 0:
                found_cat = cat_name
                break
        
        if found_cat:
            stats[found_cat] += 1
            nr_cand = counts_in_group[found_cat]
            distribution[found_cat][nr_cand] = distribution[found_cat].get(nr_cand, 0) + 1

    # --- INTERACTIVE INTERFACE ---
    while True:
        print("\n" + "="*65)
        print(" DETAILED STATISTICAL RESULTS (REVISED PRIORITY)")
        print("="*65)
        for i in range(1, 6):
            cat = category_map[i]
            val = stats[cat]
            proc = (val / total_companies) * 100
            print(f" [{i}] {cat:<45}: {val:>5} ({proc:>5.1f}%)")
        print("="*65)
        
        print("\nCommands: [1-4] Detailed Info | [q] Quit")
        cmd = input("Select a category for deep-dive: ").lower().strip()

        if cmd == 'q':
            break
        elif cmd.isdigit() and int(cmd) in range(1, 5):
            idx = int(cmd)
            cat_name = category_map[idx]
            print(f"\n" + "░"*20 + f" DETAILS: {cat_name.upper()} " + "░"*20)
            
            data_cat = distribution[cat_name]
            total_cat = stats[cat_name]
            
            if not data_cat:
                print("No candidates found in this category.")
            else:
                for nr_cand in sorted(data_cat.keys()):
                    companies_count = data_cat[nr_cand]
                    p = (companies_count / total_cat) * 100
                    
                    candidate_text = "valid candidate" if nr_cand == 1 else "valid candidates"
                    print(f" -> {nr_cand} {candidate_text} in group: {companies_count:>4} companies ({p:>5.1f}%)")
            print("░" * (45 + len(cat_name)))
        else:
            print("\n[!] Invalid command. Please choose a number between 1 and 4.")

if __name__ == "__main__":
    run_interactive_stats()