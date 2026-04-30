import pandas as pd
import numpy as np

def normalize(val):
    """Converts value to string, lowercase, and removes leading/trailing whitespace."""
    if pd.isna(val) or str(val).lower() == 'nan':
        return ""
    return str(val).strip().lower()

def extract_numbers(val):
    """Extracts only digits from a string."""
    val = normalize(val)
    return "".join(filter(str.isdigit, val))

def filtru_tara(input_row, candidates):
    """Returns candidate IDs with a matching country code."""
    input_val = normalize(input_row['input_main_country_code'])
    if not input_val: return [] 
    
    matches = []
    for i, row in candidates.iterrows():
        if normalize(row['main_country_code']) == input_val:
            matches.append(i)
    return matches

def filtru_cod_postal(input_row, candidates):
    """Returns candidate IDs where digits in the postcode match."""
    input_val = extract_numbers(input_row['input_main_postcode'])
    if not input_val: return []
    
    matches = []
    for i, row in candidates.iterrows():
        candidate_val = extract_numbers(row['main_postcode'])
        if input_val in candidate_val or candidate_val in input_val:
            if candidate_val:
                matches.append(i)
    return matches

def filtru_regiune(input_row, candidates):
    """Returns candidate IDs with a matching region."""
    input_val = normalize(input_row['input_main_region'])
    if not input_val: return []
    
    matches = []
    for i, row in candidates.iterrows():
        if normalize(row['main_region']) == input_val:
            matches.append(i)
    return matches

def filtru_strada(input_row, candidates):
    """Returns candidate IDs where the input street name is found in the record."""
    input_val = normalize(input_row['input_main_street'])
    if not input_val: return []
    
    matches = []
    for i, row in candidates.iterrows():
        if input_val in normalize(row['main_street']):
            matches.append(i)
    return matches

def filtru_nume(input_row, candidates):
    """Returns candidate IDs where company names contain one another."""
    input_val = normalize(input_row['input_company_name'])
    if not input_val: return []
    
    matches = []
    for i, row in candidates.iterrows():
        cand_name = normalize(row['company_name'])
        if input_val in cand_name or cand_name in input_val:
            matches.append(i)
    return matches