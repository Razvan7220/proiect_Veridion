import pandas as pd
import filtre as fl

df = pd.read_csv('date_companii.csv')

def get_deep_context_score(input_name, candidate_row):
    """
    Searches for missing input words across ALL metadata: 
    Descriptions, Tags, Industry, and NAICS labels.
    """
    input_tokens = fl.tokenize(input_name)
    cand_name_tokens = fl.tokenize(candidate_row['company_name'])
    
    missing_words = input_tokens - cand_name_tokens
    if not missing_words:
        return 0
    
    # Comprehensive list of text attributes to search in
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
    Tier 4 Tie-breaker: Measures how 'rich' the Veridion profile is.
    More data (revenue, employees, contact info) = higher score.
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
        
        # Apply Base Filters
        res_country = fl.filtru_tara(input_row, variants)
        res_pc      = fl.filtru_cod_postal(input_row, variants)
        res_region  = fl.filtru_regiune(input_row, variants)
        res_street  = fl.filtru_strada(input_row, variants)
        res_name_flex = fl.filtru_nume_flexibil(input_row, variants, threshold=0.1)

        qualified = []
        for i, row in variants.iterrows():
            # 1. Location Score (0-4)
            loc_score = sum([i in res_country, i in res_pc, i in res_region, i in res_street])
            
            # 2. Name Score (0.0-1.0)
            input_tokens = fl.tokenize(input_name)
            cand_tokens = fl.tokenize(row['company_name'])
            name_score = len(input_tokens.intersection(cand_tokens)) / len(input_tokens) if input_tokens else 0
            
            # 3. Context Score (Searching missing words in Tags/Industry/Desc)
            context_score = get_deep_context_score(input_name, row)
            
            # 4. Completeness Score (Tie-breaker for identical matches)
            comp_score = get_completeness_score(row)

            if i in res_name_flex and loc_score >= 2:
                qualified.append({
                    "id": i,
                    "loc_score": loc_score,
                    "name_score": name_score,
                    "context_score": context_score,
                    "comp_score": comp_score,
                    # Weighted rank: Location > Context > Name > Completeness
                    "total_rank": (loc_score * 10) + (context_score * 5) + (name_score * 2) + comp_score,
                    "veridion_id": row['veridion_id']
                })

        if not qualified:
            continue

        # Sort by the new hierarchy
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
    print(res_df['status'].value_counts().to_string())
    return res_df

if __name__ == "__main__":
    report = resolve_category_1()
    
    ties = report[report['status'] == "Absolute Tie"]
    if not ties.empty:
        print("\n" + "!"*60)
        print(f" UNRESOLVED KEYS ({len(ties)}) - REMAINING TIES")
        print("!"*60)
        for _, row in ties.iterrows():
            print(f"Key: {row['key']} | VID: {row['vid']} | Loc: {row['loc']} | Name: {row['name']}")