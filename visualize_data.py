import pandas as pd

# Încarcă datele
try:
    df = pd.read_csv('date_companii.csv')
except FileNotFoundError:
    print("[!] Eroare: Nu am găsit fișierul 'date_companii.csv' în folder.")
    exit()

def afiseaza_interfata(row_key, deep_dive_idx=None):
    # 1. Filtrăm variantele pentru cheia curentă
    variante = df[df['input_row_key'] == row_key].reset_index(drop=True)
    
    if variante.empty:
        print(f"\n[!] Cheia {row_key} nu există.")
        return

    input_data = variante.iloc[0]
    
    # 2. VIZUALIZARE LINIARĂ COMPLETĂ INPUT (Toate cele 8 coloane)
    print("\n" + "█"*145)
    print(f" LINEAR INPUT VIEW (Client Data) - Key: {row_key}")
    print("-" * 145)
    
    headers = ["NAME", "CODE", "COUNTRY", "REGION", "CITY", "P-CODE", "STREET", "NR"]
    widths = [30, 5, 12, 15, 15, 8, 20, 5]
    
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("-" * 145)
    
    # Extragem toate cele 8 valori de input
    v_nume = str(input_data['input_company_name'])[:30].ljust(30)
    v_code = str(input_data['input_main_country_code']).ljust(5)
    v_ctry = str(input_data['input_main_country'])[:12].ljust(12)
    v_reg  = str(input_data['input_main_region'])[:15].ljust(15)
    v_city = str(input_data['input_main_city'])[:15].ljust(15)
    v_post = str(input_data['input_main_postcode'])[:8].ljust(8)
    v_str  = str(input_data['input_main_street'])[:20].ljust(20)
    v_nr   = str(input_data['input_main_street_number']).ljust(5)
    
    print(f"{v_nume} | {v_code} | {v_ctry} | {v_reg} | {v_city} | {v_post} | {v_str} | {v_nr}")
    print("█" + "━"*143 + "█")

    # 3. LISTA VARIANTE VERIDION
    print(f"{'ID':<4} | {'NUME COMPANIE GASITA (Veridion)':<40} | {'TARA':<5} | {'MATCH TARA'}")
    print("-" * 95)

    for i, (index, row) in enumerate(variante.iterrows()):
        nume_v = str(row['company_name'])[:40].ljust(40)
        tara_v = str(row['main_country_code'])
        tara_i = str(input_data['input_main_country_code'])
        match_tara = "[OK]" if tara_v == tara_i else "[!!]"
        
        pointer = " >> " if deep_dive_idx == i else "    "
        print(f"{pointer}{i:<2} | {nume_v} | {tara_v:<5} | {match_tara}")

    # 4. DEEP DIVE
    if deep_dive_idx is not None and deep_dive_idx < len(variante):
        print("\n" + "░"*40 + f" DETALII COMPLETE VARIANTA {deep_dive_idx} " + "░"*40)
        v_data = variante.iloc[deep_dive_idx]
        coloane_veridion = [col for col in df.columns if not col.startswith('input_')]
        for col in coloane_veridion:
            val = v_data[col]
            if pd.notnull(val):
                print(f"{col:<30}: {val}")
        print("░"*105)

# --- BUCLA INTERACTIVĂ ---
current_key = 0
v_selectata = None

while True:
    afiseaza_interfata(current_key, deep_dive_idx=v_selectata)
    
    print(f"\nCOMENZI: [n] Next | [p] Prev | [v + ID] Detalii (ex: v0) | [c] Clear | [key_number] Sari la cifra | [q] Quit")
    comanda = input(f"(Curent: {current_key}) Alege o comanda: ").lower().strip()

    if comanda == 'n':
        current_key += 1
        v_selectata = None
    elif comanda == 'p':
        current_key = max(0, current_key - 1)
        v_selectata = None
    elif comanda == 'c':
        v_selectata = None
    elif comanda.startswith('v'):
        try:
            v_selectata = int(comanda[1:])
        except ValueError:
            print("[!] Folosește formatul v0, v1, etc.")
    elif comanda == 'q':
        print("La revedere!")
        break
    elif comanda.isdigit():
        current_key = int(comanda)
        v_selectata = None
    else:
        print("\n[!] Comandă invalidă.")