import os
import json
from curl_cffi import requests

data = [
  {
    "name": "WD Red Pro",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/internal-storage/wd-red-pro-sata-hdd/gallery/wd-red-pro-main-nocap.png"
  },
  {
    "name": "WD Red Plus",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/internal-storage/wd-red-plus-sata-3-5-hdd/gallery/wd-red-plus-sata-3-5-hdd-main-nocap.png"
  },
  {
    "name": "My Passport Ultra",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/portable/my-passport-ultra/gallery/silver/1tb/my-passport-ultra-1tb-WDBC3C0010BSL-WESN-front-12mm-silver.png"
  },
  {
    "name": "WD Blue Mobile",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/internal-storage/wd-blue-mobile-sata-hdd/gallery/wd-blue-mobile-main-nocap.png"
  },
  {
    "name": "WD Blue",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/internal-storage/wd-blue-desktop-sata-hdd/gallery/CampaignThumbnail.png"
  },
  {
    "name": "My Passport USB-C",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/portable/my-passport-phdd-usb-c/gallery/my-passport-phdd-usb-c-2tb-left.png"
  },
  {
    "name": "My Passport",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/portable/my-passport/gallery/black/1-2tb/MyPassport-1TB-2TB-Black-Hero.png"
  },
  {
    "name": "My Passport for Mac",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/portable/my-passport-for-mac-new/gallery/2tb/MyPassport-for-Mac-1-2TB-Midnight-Blue-Hero.png"
  },
  {
    "name": "WD Purple Pro",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/internal-storage/wd-purple-pro-sata-hdd/gallery/wd-purple-pro-sata-hdd-main-nocap.png"
  },
  {
    "name": "WD Purple",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/internal-storage/wd-purple-sata-hdd/gallery/wd-purple-surveillance-hard-drive-main-nocap.png"
  },
  {
    "name": "My Passport Ultra for Mac",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/portable/my-passport-ultra-for-mac/gallery/2tb/my-passport-ultra-for-mac-2tb-WDBKYJ0020BSL-WESN-front-12mm-Silver.png"
  },
  {
    "name": "WD Black",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/internal-storage/wd-black-desktop-sata-hdd/gallery/wd-black-desktop-1tb.png"
  },
  {
    "name": "WD Black Mobile",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/internal-storage/wd-black-mobile-sata-hdd/gallery/wd-black-mobile-sata-hdd-left-500gb.png"
  },
  {
    "name": "WD Black P10",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/desktop/wd-black-p10-game-drive-usb-3-2-hdd/gallery/2tb/WD-Black-P10-Game-Drive-2TB-Hero.png"
  },
  {
    "name": "WD Gold",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/internal-storage/wd-gold-sata-hdd/gallery/WD-GOLD-main-nocap.png"
  },
  {
    "name": "WD Elements Portable",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/portable/wd-elements-portable/gallery/1tb/wd-elements-portable-1-2tb-front.png"
  },
  {
    "name": "WD Elements Desktop",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/desktop/wd-elements-desktop-usb-3-0-hdd/gallery/wd-elements-desktop-right.png"
  },
  {
    "name": "WD Elements SE",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/portable/wd-elements-se/gallery/1tb/wd-elements-se-1-2tb-front.png"
  },
  {
    "name": "My Book",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/desktop/my-book-usb-3-0-hdd/gallery/my-book-new-front-2.png"
  },
  {
    "name": "My Book Duo",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/desktop/my-book-duo-usb-3-1-hdd/gallery/my-book-duo-hero.png"
  },
  {
    "name": "WD Black D10",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/desktop/wd-black-d10-game-drive/gallery/WD_Black_D10_Game_Drive_Hero.png"
  },
  {
    "name": "Ultrastar",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/internal-storage/ultrastar-dc-hc690-hdd/gallery/ultrastar-dc-hc690-hdd-nocap.png"
  },
  {
    "name": "G-DRIVE",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/desktop/g-drive-usb-c-hdd/gallery/g-drive-usb-c-hdd-left.png"
  },
  {
    "name": "WD Red",
    "image": "https://www.westerndigital.com/content/dam/store/en-us/assets/products/internal-storage/wd-red-sata-hdd/gallery/wd-red-3-5-2tb.png"
  }
]

os.makedirs("static/images", exist_ok=True)
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def slugify(name):
    return "wd_" + name.lower().replace(" ", "_").replace("-", "_").replace("\"", "").replace(",", "")

for item in data:
    name_slug = slugify(item['name']) + '.png'
    url = item['image']
    filepath = os.path.join("static/images", name_slug)
    
    # avoid re-downloading existing images to save time, unless it's Red or My Passport etc
    # Actually just download them all since it's the requested source of truth.
    print(f"Downloading {name_slug} from {url}...")
    try:
        res = requests.get(url, impersonate="chrome120", headers=headers)
        if res.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(res.content)
            print(f"  -> Saved {len(res.content)} bytes")
        else:
            print(f"  -> Failed {res.status_code}")
    except Exception as e:
        print(f"  -> Error: {e}")
