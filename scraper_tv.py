import os
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

# ==========================================================
# 1. NASTAVITVE TRGOVIN PO DRŽAVAH IN KATEGORIJAH
# ==========================================================
# Tukaj poljubno dodajaj ali briši trgovine. 
# Ime mora biti del URL-ja (npr. 'hofer' za katalog24.si/katalog/hofer-...)

NASTAVITVE_TRGOVIN = {
    "si": {
        "zivila": ["hofer", "lidl", "spar", "mercator", "eurospin", "jager", "tus"],
        "tehnika": ["big-bang", "harvey-norman", "m-tehnika"]
    },
    "hr": {
        "prehrana": ["konzum", "lidl", "kaufland", "spar", "plodine", "tommy"],
        "tehnika": ["pevex", "elipso", "sancta-domenica"]
    },
    "at": {
        "lebensmittel": ["hofer", "lidl", "billa", "spar", "penny", "mpreis"],
        "elektronik": ["media-markt", "conrad", "hartlauer"]
    },
    "it": {
        "alimentari": ["eurospin", "conad", "coop", "lidl", "carrefour", "esselunga"],
        "elettronica": ["media-world", "unieuro", "euronics"]
    }
}

ST_KATALOGOV_NA_TRGOVINO = 2  # Koliko najnovejših na trgovino
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ==========================================================
# 2. LOGIKA (Spreminjanje ni potrebno)
# ==========================================================

BASE_URLS = {
    "si": "https://katalog24.si",
    "hr": "https://katalog24.hr",
    "at": "https://flugblatt24.at",
    "it": "https://volantini24.it"
}

def get_store_name_clean(title):
    """Iz naslova naredi lepše ime za aplikacijo."""
    words = title.split(' ')
    if len(words) > 1:
        prefix = f"{words[0]} {words[1]}".lower()
        if prefix in ["big bang", "baby center", "m tehnika", "media markt", "media world", "harvey norman"]:
            return f"{words[0]} {words[1]}"
    return words[0]

def extract_date(text):
    iso = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if iso: return f"{iso.group(1)}-{iso.group(2)}-{iso.group(3)}"
    slo_at = re.search(r'(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4})', text)
    if slo_at: return f"{slo_at.group(3)}-{slo_at.group(2).zfill(2)}-{slo_at.group(1).zfill(2)}"
    return datetime.now().strftime("%Y-%m-%d")

def get_catalog_content(url, country_code):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        h1 = soup.find('h1').text.strip() if soup.find('h1') else "Katalog"
        
        images = []
        for img in soup.find_all('img'):
            src = img.get('data-src') or img.get('src')
            if src and any(ext in src for ext in ['.jpg', '.jpeg', '.png']):
                if not any(x in src.lower() for x in ["logo", "icon", "thumb", "social"]):
                    images.append(urljoin(BASE_URLS[country_code], src))
        
        return {
            "trgovina": get_store_name_clean(h1),
            "naslov": h1,
            "datum": extract_date(h1),
            "slike": images
        }
    except:
        return None

def main():
    baza_podatkov = {}

    for d_kod, kategorije in NASTAVITVE_TRGOVIN.items():
        baza_podatkov[d_kod] = {}
        base_url = BASE_URLS[d_kod]
        
        for kat, dovoljene_trgovine in kategorije.items():
            print(f">>> Obdelujem: {d_kod.upper()} - {kat}")
            baza_podatkov[d_kod][kat] = []
            
            cat_url = f"{base_url}/kategorija/{kat}"
            try:
                res = requests.get(cat_url, headers=HEADERS)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Zberemo samo tiste linke, ki so na našem seznamu dovoljenih trgovin
                links_per_store = {t: [] for t in dovoljene_trgovine}
                
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if any(x in href for x in ['/katalog/', '/volantino/', '/prospekt/']):
                        # Preverimo, če je katera od naših trgovin v URL-ju
                        for trgovina in dovoljene_trgovine:
                            if f"/{trgovina}-" in href or f"/{trgovina}/" in href or href.endswith(trgovina):
                                full_url = urljoin(base_url, href)
                                if full_url not in links_per_store[trgovina]:
                                    links_per_store[trgovina].append(full_url)
                
                # Dejanski prenos podatkov za izbrane kataloge
                for trgovina, urls in links_per_store.items():
                    for link in urls[:ST_KATALOGOV_NA_TRGOVINO]:
                        data = get_catalog_content(link, d_kod)
                        if data:
                            baza_podatkov[d_kod][kat].append(data)
                            print(f"    Dodan: {data['naslov']}")
            except Exception as e:
                print(f"    Napaka pri kategoriji {kat}: {e}")

    # Shranjevanje v JSON
    with open('katalogi.json', 'w', encoding='utf-8') as f:
        json.dump(baza_podatkov, f, ensure_ascii=False, indent=4)
    print("\nUspeh! Datoteka 'katalogi.json' je pripravljena za TV aplikacijo.")

if __name__ == "__main__":
    main()
