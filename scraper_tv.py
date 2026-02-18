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

ST_KATALOGOV_NA_TRGOVINO = 2  
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
MIN_FILE_SIZE = 80000  # Minimalna velikost v bajtih (80 KB)

# ==========================================================
# 2. LOGIKA
# ==========================================================

BASE_URLS = {
    "si": "https://katalog24.si",
    "hr": "https://katalog24.hr",
    "at": "https://flugblatt24.at",
    "it": "https://volantini24.it"
}

def get_store_name_clean(title):
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
        catalog_area = soup.find('div', {'class': 'catalog-view'}) or soup
        
        for img in catalog_area.find_all('img'):
            src = img.get('data-src') or img.get('src')
            if src:
                src_lower = src.lower()
                # Filtriranje po končnici
                if any(ext in src_lower for ext in ['.jpg', '.jpeg']):
                    # Strogo izločanje logotipov po imenu
                    if any(x in src_lower for x in ["logo", "icon", "thumb", "social", "media", "png"]):
                        continue
                    
                    full_img_url = urljoin(BASE_URLS[country_code], src)
                    
                    # PREVERJANJE VELIKOSTI (ignoriraj manjše od 80KB)
                    try:
                        # Pošljemo samo HEAD zahtevek, da dobimo velikost brez prenosa slike
                        head = requests.head(full_img_url, headers=HEADERS, timeout=5)
                        size = int(head.headers.get('Content-Length', 0))
                        
                        if size >= MIN_FILE_SIZE:
                            if full_img_url not in images:
                                images.append(full_img_url)
                    except:
                        # Če HEAD ne uspe, sliko dodamo le, če URL zgleda kot prava stran
                        if "featured_image" in src_lower or "/m2/" in src_lower:
                            if full_img_url not in images:
                                images.append(full_img_url)
        
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
            print(f"\n>>> Obdelujem: {d_kod.upper()} - {kat}")
            baza_podatkov[d_kod][kat] = []
            
            cat_url = f"{base_url}/kategorija/{kat}"
            try:
                res = requests.get(cat_url, headers=HEADERS)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                links_per_store = {t: [] for t in dovoljene_trgovine}
                
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if any(x in href for x in ['/katalog/', '/volantino/', '/prospekt/']):
                        for trgovina in dovoljene_trgovine:
                            if f"/{trgovina}-" in href or f"/{trgovina}/" in href or href.endswith(trgovina):
                                full_url = urljoin(base_url, href)
                                if full_url not in links_per_store[trgovina]:
                                    links_per_store[trgovina].append(full_url)
                
                for trgovina, urls in links_per_store.items():
                    for link in urls[:ST_KATALOGOV_NA_TRGOVINO]:
                        data = get_catalog_content(link, d_kod)
                        if data and data['slike']: # Dodamo le, če smo našli slike > 80KB
                            baza_podatkov[d_kod][kat].append(data)
                            print(f"    Dodan: {data['naslov']} ({len(data['slike'])} slik)")
            except Exception as e:
                print(f"    Napaka pri kategoriji {kat}: {e}")

    with open('katalogi.json', 'w', encoding='utf-8') as f:
        json.dump(baza_podatkov, f, ensure_ascii=False, indent=4)
    print("\nUspeh! Datoteka 'katalogi.json' je pripravljena.")

if __name__ == "__main__":
    main()
