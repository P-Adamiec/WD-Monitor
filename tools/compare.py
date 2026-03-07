import sys
from bs4 import BeautifulSoup
from curl_cffi import requests

URL_IN_STOCK = "https://www.westerndigital.com/pl-pl/products/internal-drives/wd-purple-pro-sata-hdd?sku=WD221PURP"
URL_OUT_OF_STOCK = "https://www.westerndigital.com/pl-pl/products/internal-drives/wd-red-pro-sata-hdd?sku=WD8005FFBX"

r1 = requests.get(URL_IN_STOCK, impersonate="chrome120", timeout=15)
r2 = requests.get(URL_OUT_OF_STOCK, impersonate="chrome120", timeout=15)

text1 = r1.text
text2 = r2.text

print(f"IN STOCK length: {len(text1)}")
print(f"OUT OF STOCK length: {len(text2)}")

stock_terms = ['inStock', 'outOfStock', 'stockLevel', '"stockStatus":"', "'stockStatus':'", 'out-of-stock', 'oos']
for term in stock_terms:
    c1 = text1.count(term)
    c2 = text2.count(term)
    if c1 != c2:
        print(f"Term '{term}': IN_STOCK={c1}, OUT_OF_STOCK={c2}")
