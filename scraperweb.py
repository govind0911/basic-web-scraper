import requests
from bs4 import BeautifulSoup

url = input("Enter URL: ").strip()

if url == "":
    print("No URL entered. Exiting.")
    exit()

if not url.startswith("http://") and not url.startswith("https://"):
    url = "https://" + url

try:
    r = requests.get(url, timeout=10)
except requests.exceptions.RequestException as e:
    print("Request error:", e)
    exit()

if r.status_code != 200:
    print("Request failed with status code:", r.status_code)
    exit()

soup = BeautifulSoup(r.text, "html.parser")

title = soup.title.text.strip() if soup.title else "No title found"
print("\nPage Title:", title)

paragraphs = soup.find_all("p")

if not paragraphs:
    print("\nNo paragraph text found.")
else:
    print("\nExtracted text:")
    for i, p in enumerate(paragraphs[:10], 1):
        print(f"{i}. {p.get_text(strip=True)}")

print("\nScraping completed successfully.")
