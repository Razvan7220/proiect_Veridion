import pandas as pd
import filtre as fl

# Load the data
df = pd.read_csv('date_companii.csv')

def get_deep_context_score(input_name, candidate_row):
    """
    Searches for missing input words across descriptions, tags, and industry labels.
    """
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
    """
    Measures profile richness (revenue, employees, contact info) as a final tie-breaker.
    """
    rich_fields = [
        'revenue', 'employee_count', 'primary_email', 
        'primary_phone', 'year_founded', 'main_business_category'
    ]
    score = sum(1 for field in rich_fields if pd.notnull(row.get(field)) and str(row.get(field)).lower() != 'nan')
    return score / len(rich_fields)

def resolve_category_1():
    all_keys = df['input_row_key'].unique()
    final_results = []

    for key in all_keys:
        variants = df[df['input_row_key'] == key].reset_index(drop=True)
        input_row = variants.iloc[0]
        input_name = input_row['input_company_name']
        
        # Apply All Location Filters
        res_country = fl.filtru_tara(input_row, variants)
        res_pc      = fl.filtru_cod_postal(input_row, variants)
        res_region  = fl.filtru_regiune(input_row, variants)
        res_street  = fl.filtru_strada(input_row, variants)
        res_city    = fl.filtru_oras(input_row, variants)
        res_number  = fl.filtru_numar_strada(input_row, variants)
        res_raw_loc = fl.filtru_locations_brut(input_row, variants)
        
        # Apply Name Filter
        res_name_flex = fl.filtru_nume_flexibil(input_row, variants, threshold=0.1)

        qualified = []
        for i, row in variants.iterrows():
            # 1. New Location Score (Sum of 7 attributes)
            loc_score = sum([
                i in res_country, 
                i in res_pc, 
                i in res_region, 
                i in res_street,
                i in res_city,
                i in res_number,
                i in res_raw_loc
            ])
            
            # 2. Name Score
            input_tokens = fl.tokenize(input_name)
            cand_tokens = fl.tokenize(row['company_name'])
            name_score = len(input_tokens.intersection(cand_tokens)) / len(input_tokens) if input_tokens else 0
            
            # 3. Context & Completeness
            context_score = get_deep_context_score(input_name, row)
            comp_score = get_completeness_score(row)

            # Inclusion criteria: Name match + at least 2 location points
            if i in res_name_flex and loc_score >= 2:
                qualified.append({
                    "id": i,
                    "loc_score": loc_score,
                    "name_score": name_score,
                    "context_score": context_score,
                    "comp_score": comp_score,
                    # Weight: Location remains the primary driver
                    "total_rank": (loc_score * 10) + (context_score * 5) + (name_score * 2) + comp_score,
                    "veridion_id": row['veridion_id']
                })

        if not qualified:
            continue

        # Hierarchical Sort
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
            "key": key, "status": status, "best_id": best['id'],
            "loc": best['loc_score'], "name": round(best['name_score'], 2),
            "context": round(best['context_score'], 2), "vid": best['veridion_id']
        })

    res_df = pd.DataFrame(final_results)
    if not res_df.empty:
        print("\n=== RESOLUTION SUMMARY ===")
        print(res_df['status'].value_counts().to_string())
    return res_df

if __name__ == "__main__":
    report = resolve_category_1()
    
    if not report.empty:
        ties = report[report['status'] == "Absolute Tie"]
        if not ties.empty:
            print("\n" + "!"*60)
            print(f" UNRESOLVED KEYS ({len(ties)}) - REMAINING TIES")
            print("!"*60)
            for _, row in ties.iterrows():
                print(f"Key: {row['key']} | VID: {row['vid']} | Loc Score: {row['loc']}/7 | Name Score: {row['name']}")
    else:
        print("No qualified matches found for Category 1.")