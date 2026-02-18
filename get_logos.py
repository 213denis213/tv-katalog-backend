import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

# Seznam URL-jev za vse države
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
        print(f"\n>>> Preverjam državo: {d_kod.upper()}")
        logotipi_baza[d_kod] = {}
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Najdemo vse slike na strani
            all_imgs = soup.find_all('img')
            najdeno_za_drzavo = 0
            
            for img in all_imgs:
                # Preverimo vse možne atribute, kjer bi se lahko skrival URL slike
                src = img.get('data-src') or img.get('src') or img.get('data-original')
                
                if src:
                    src_lower = src.lower()
                    
                    # HRVAŠKA IN AVSTRIJA: Logotipi so pogosto v /media/ ali vsebujejo ime trgovine v URL-ju
                    # SLOVENIJA IN ITALIJA: Logotipi so v /images/shops/
                    is_logo = any(x in src_lower for x in ["/images/shops/", "/media/", "/shops/", "/logo/"])
                    
                    if is_logo:
                        # Izognemo se generičnim ikonam
                        if any(bad in src_lower for bad in ["facebook", "instagram", "twitter", "yt.png", "li.png"]):
                            continue
                            
                        full_logo_url = urljoin(url, src)
                        
                        # Ime trgovine iz URL-ja (vzame zadnji del pred končnico)
                        # npr. iz '.../media/konzum.png' dobi 'konzum'
                        store_id = src.split('/')[-1].split('.')[0].lower()
                        
                        # Če ime trgovine vsebuje čudne znake (npr. 0-katalog24), ga očistimo
                        if "-" in store_id:
                            store_id = store_id.split('-')[-1]
                            
                        logotipi_baza[d_kod][store_id] = full_logo_url
                        najdeno_za_drzavo += 1
            
            print(f"    Uspeh! Najdenih {najdeno_za_drzavo} logotipov.")
            
        except Exception as e:
            print(f"    Napaka pri {d_kod}: {e}")

    # Shranimo v JSON
    with open('trgovine_logotipi.json', 'w', encoding='utf-8') as f:
        json.dump(logotipi_baza, f, ensure_ascii=False, indent=4)
    
    print("\nKončano! Preveri datoteko 'trgovine_logotipi.json' v repozitoriju.")

if __name__ == "__main__":
    scrape_logos()
