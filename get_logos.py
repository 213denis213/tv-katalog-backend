import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

BASE_URLS = {
    "si": "https://katalog24.si/trgovine",
    "hr": "https://katalog24.hr/trgovine",
    "at": "https://flugblatt24.at/geschafte",
    "it": "https://volantini24.it/negozi"
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def scrape_logos():
    logotipi_baza = {}

    for d_kod, url in BASE_URLS.items():
        print(f"Pobiram logotipe za: {d_kod.upper()}")
        logotipi_baza[d_kod] = {}
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Poiščemo vse kartice trgovin
            # Običajno so v <a> značkah, ki vsebujejo sliko logotipa
            for a in soup.find_all('a', href=True):
                img = a.find('img')
                if img:
                    src = img.get('data-src') or img.get('src')
                    # Preverimo, če je URL v mapi /images/shops/
                    if src and "/images/shops/" in src:
                        # Očistimo ime trgovine iz URL-ja ali href-a
                        # npr. iz 'hofer.jpg' dobimo 'hofer'
                        store_id = src.split('/')[-1].split('.')[0].lower()
                        full_logo_url = urljoin(url, src)
                        
                        logotipi_baza[d_kod][store_id] = full_logo_url
        except Exception as e:
            print(f"Napaka pri {d_kod}: {e}")

    # Shranimo v ločeno JSON datoteko
    with open('trgovine_logotipi.json', 'w', encoding='utf-8') as f:
        json.dump(logotipi_baza, f, ensure_ascii=False, indent=4)
    
    print("\nKončano! Ustvarjena datoteka: trgovine_logotipi.json")

if __name__ == "__main__":
    scrape_logos()
