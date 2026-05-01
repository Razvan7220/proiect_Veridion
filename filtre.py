import pandas as pd
import numpy as np
import re

def tokenize(text):
    """
    Advanced tokenizer that preserves abbreviations and hyphenated words.
    - Keeps: A/S, MG-H, 3-M, etc.
    - Removes: standalone punctuation and spaces.
    """
    if not text or pd.isna(text):
        return set()
        
    # 1. Normalize to lowercase
    text = text.lower().strip()
    
    # 2. Regex logic:
    # \b[\w\d]+          -> Starts with alphanumeric characters
    # (?:[-/][\w\d]+)*   -> Optionally followed by (-) or (/) and more alphanumeric chars
    # \b                 -> Ends at a word boundary
    pattern = r'\b[\w\d]+(?:[-/][\w\d]+)*\b'
    
    tokens = re.findall(pattern, text)
    
    # We no longer filter by len(w) > 1 because 'A/S' or 'MG-H' 
    # are now captured as single tokens, and even single letters 
    # can be critical in abbreviations.
    return set(tokens)

def filtru_nume_flexibil(input_row, candidates, threshold=0.5):
    """
    Middle-ground filter: checks what percentage of input words 
    exist in the candidate name.
    
    threshold=0.65 means at least 65% of input words must match.
    Example: 'ACCENTURE SERVICES AS' (3 words) 
    - Match with 'ACCENTURE SERVICES' -> 2/3 = 66% (PASSES)
    - Match with 'ACCENTURE' -> 1/3 = 33% (FAILS)
    """
    input_name = input_row['input_company_name']
    input_words = tokenize(input_name)
    
    if not input_words: 
        return []
    
    matches = []
    for i, row in candidates.iterrows():
        candidate_name = row['company_name']
        candidate_words = tokenize(candidate_name)
        
        if not candidate_words:
            continue
            
        # Intersection: words found in both sets
        common_words = input_words.intersection(candidate_words)
        
        # Calculate matching score (0.0 to 1.0)
        match_score = len(common_words) / len(input_words)
        
        if match_score >= threshold:
            matches.append(i)
            
    return matches

def filtru_nume_rigid(input_row, candidates):
    """
    Strict 'Bag of Words' filter. Every word in the input name MUST exist 
    within the candidate's name for it to pass.
    
    Example: 
    Input: 'ACCENTURE SERVICES AS' 
    Match: 'ACCENTURE CLOUD SERVICES AS' (Contains all 3 words)
    No Match: 'ACCENTURE SERVICES' (Missing 'AS')
    """
    input_name = input_row['input_company_name']
    input_words = tokenize(input_name)
    
    if not input_words: 
        return []
    
    matches = []
    for i, row in candidates.iterrows():
        candidate_name = row['company_name']
        candidate_words = tokenize(candidate_name)
        
        # Check if the input word set is a subset of the candidate word set
        if input_words.issubset(candidate_words):
            matches.append(i)
            
    return matches

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