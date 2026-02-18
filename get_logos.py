import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

# Posodobljeni URL-ji za vse države
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
        print(f"Pobiram logotipe za: {d_kod.upper()}...")
        logotipi_baza[d_kod] = {}
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Iščemo vse slike na strani, ki so v mapi /images/shops/
            all_imgs = soup.find_all('img')
            
            for img in all_imgs:
                src = img.get('data-src') or img.get('src')
                if src and "/images/shops/" in src:
                    # Pridobimo polno pot do slike
                    full_logo_url = urljoin(url, src)
                    
                    # Ime trgovine iz URL-ja (npr. hofer iz .../hofer.jpg)
                    store_id = src.split('/')[-1].split('.')[0].lower()
                    
                    # Preprečimo dodajanje generičnih ikon, če obstajajo
                    if any(x in store_id for x in ["logo", "default", "placeholder"]):
                        continue
                        
                    logotipi_baza[d_kod][store_id] = full_logo_url
            
            print(f"   Najdenih logotipov za {d_kod.upper()}: {len(logotipi_baza[d_kod])}")
            
        except Exception as e:
            print(f"   Napaka pri {d_kod}: {e}")

    # Shranimo v JSON datoteko
    with open('trgovine_logotipi.json', 'w', encoding='utf-8') as f:
        json.dump(logotipi_baza, f, ensure_ascii=False, indent=4)
    
    print("\nUspeh! 'trgovine_logotipi.json' zdaj vsebuje podatke za vse države.")

if __name__ == "__main__":
    scrape_logos()
