import os
import json
import re
from curl_cffi import requests
from bs4 import BeautifulSoup

urls = {
    "wd_red_pro.png": "https://www.westerndigital.com/pl-pl/products/internal-drives/wd-red-pro-sata-hdd",
    "wd_purple_pro.png": "https://www.westerndigital.com/pl-pl/products/internal-drives/wd-purple-pro-sata-hdd",
    "wd_gold.png": "https://www.westerndigital.com/pl-pl/products/internal-drives/wd-gold-sata-hdd",
    "wd_black.png": "https://www.westerndigital.com/pl-pl/products/internal-drives/wd-black-desktop-sata-hdd",
    "wd_red_plus.png": "https://www.westerndigital.com/pl-pl/products/internal-drives/wd-red-plus-sata-hdd",
    "wd_blue.png": "https://www.westerndigital.com/pl-pl/products/internal-drives/wd-blue-pc-desktop-hard-drive",
    "wd_ultrastar.png": "https://www.westerndigital.com/pl-pl/products/internal-drives/ultrastar-dc-hc560-sata-hdd"
}

os.makedirs("static/images", exist_ok=True)

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

for name, url in urls.items():
    print(f"Scraping image for {name} from {url}...")
    try:
        response = requests.get(url, impersonate="chrome120", headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for og:image
            og_image = soup.find('meta', property='og:image')
            
            img_url = None
            if og_image and og_image.get('content'):
                img_url = og_image.get('content')
            else:
                # Try finding JSON data in scripts
                print(f"No og:image for {name}, trying regex on HTML...")
                matches = re.findall(r'"image"\s*:\s*"([^"]+\.png[^"]*)"', response.text)
                if matches:
                    img_url = matches[0]
            
            if img_url:
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    img_url = "https://www.westerndigital.com" + img_url
                    
                print(f"Found image URL: {img_url}. Downloading...")
                img_res = requests.get(img_url, impersonate="chrome120", headers=headers)
                if img_res.status_code == 200:
                    with open(os.path.join("static/images", name), "wb") as f:
                        f.write(img_res.content)
                    print(f"SAVED {name}")
                else:
                    print(f"Failed to download image file for {name}, status: {img_res.status_code}")
            else:
                print(f"Could not find any image URL in HTML for {name}")
        else:
            print(f"Failed to load page for {name} with status {response.status_code}")
    except Exception as e:
        print(f"Error {name}: {e}")
