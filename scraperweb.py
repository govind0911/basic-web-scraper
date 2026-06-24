import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import Counter
import json
import logging
import re

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)

MAX_PARAGRAPHS_DISPLAY = 10
TOP_KEYWORDS = 20

try:
    logging.basicConfig(
        filename="scraper.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
except Exception:
    logging.basicConfig(level=logging.INFO)

def validate_url(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

def fetch_page(url):
    headers = {"User-Agent": USER_AGENT}

    try:
        print("\n[+] Downloading page...")

        response = requests.get(
            url,
            headers=headers,
            timeout=15,
            allow_redirects=True
        )

        response.raise_for_status()

        if not response.encoding:
            response.encoding = response.apparent_encoding

        logging.info(f"Fetched page: {response.url}")

        return response

    except requests.exceptions.Timeout:
        print("[-] Request timed out.")
    except requests.exceptions.SSLError:
        print("[-] SSL certificate verification failed.")
    except requests.exceptions.ConnectionError:
        print("[-] Connection failed.")
    except requests.exceptions.RequestException as e:
        print(f"[-] Request Error: {e}")

    return None

def extract_page_data(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    title = "No title"
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})

    meta_description = "No description"
    if meta_desc_tag:
        content = meta_desc_tag.get("content")
        if content:
            meta_description = content.strip()

    headings = []

    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            text = tag.get_text(" ", strip=True)
            if text:
                headings.append({
                    "level": f"H{level}",
                    "text": text
                })

    paragraphs = []

    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text:
            paragraphs.append(text)

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()

        if href.startswith(("javascript:", "mailto:", "tel:")):
            continue

        links.append(urljoin(base_url, href))

    links = list(set(links))

    images = []

    for img in soup.find_all("img", src=True):
        src = img["src"].strip()

        if src.startswith("data:"):
            continue

        images.append(urljoin(base_url, src))

    images = list(set(images))

    full_text = " ".join(paragraphs)

    words = re.findall(r"\b[a-zA-Z]{3,}\b", full_text.lower())

    stop_words = {
        "the", "and", "for", "with", "that",
        "this", "you", "your", "are", "was",
        "from", "have", "has", "had", "will",
        "not", "but", "all", "can", "our",
        "their", "they", "them", "about",
        "into", "out", "what", "when",
        "where", "which", "who"
    }

    filtered_words = [
        word for word in words
        if word not in stop_words
    ]

    keyword_counts = Counter(filtered_words)

    keywords = (
        keyword_counts.most_common(TOP_KEYWORDS)
        if keyword_counts
        else [("No keywords", 0)]
    )

    return {
        "title": title,
        "description": meta_description,
        "headings": headings,
        "paragraphs": paragraphs,
        "links": links,
        "images": images,
        "word_count": len(words),
        "keywords": keywords
    }

def save_json(data):
    filename = "scraped_data.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(f"\n[+] JSON saved -> {filename}")

def save_txt(data):
    filename = "scraped_data.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Title: {data['title']}\n\n")
        f.write(f"Description: {data['description']}\n\n")

        f.write("HEADINGS\n")
        f.write("=" * 50 + "\n")

        for heading in data["headings"]:
            f.write(f"{heading['level']}: {heading['text']}\n")

        f.write("\nPARAGRAPHS\n")
        f.write("=" * 50 + "\n")

        for i, p in enumerate(data["paragraphs"], 1):
            f.write(f"{i}. {p}\n\n")

        f.write("\nLINKS\n")
        f.write("=" * 50 + "\n")

        for link in data["links"]:
            f.write(link + "\n")

        f.write("\nIMAGES\n")
        f.write("=" * 50 + "\n")

        for image in data["images"]:
            f.write(image + "\n")

        f.write("\nTOP KEYWORDS\n")
        f.write("=" * 50 + "\n")

        for word, count in data["keywords"]:
            f.write(f"{word}: {count}\n")

    print(f"[+] TXT saved -> {filename}")

def display_summary(data):
    print("\n" + "=" * 60)
    print("SCRAPING RESULTS")
    print("=" * 60)

    print(f"\nTitle: {data['title']}")
    print(f"Description: {data['description']}")

    print(f"\nHeadings Found: {len(data['headings'])}")
    print(f"Paragraphs Found: {len(data['paragraphs'])}")
    print(f"Links Found: {len(data['links'])}")
    print(f"Images Found: {len(data['images'])}")
    print(f"Word Count: {data['word_count']}")

    print("\nTop Keywords:")

    for word, count in data["keywords"]:
        print(f"  {word}: {count}")

    print("\nSample Paragraphs:\n")

    for i, paragraph in enumerate(
        data["paragraphs"][:MAX_PARAGRAPHS_DISPLAY],
        start=1
    ):
        preview = (
            paragraph[:250] + "..."
            if len(paragraph) > 250
            else paragraph
        )

        print(f"{i}. {preview}\n")

def main():
    print("=" * 60)
    print("ADVANCED WEB SCRAPER")
    print("=" * 60)

    url = input("\nEnter URL: ").strip()

    if not url:
        print("No URL entered.")
        return

    url = validate_url(url)

    response = fetch_page(url)

    if not response:
        return

    print(f"\n[+] Final URL: {response.url}")
    print(f"[+] Status Code: {response.status_code}")

    data = extract_page_data(
        response.text,
        response.url
    )

    display_summary(data)

    save_json(data)
    save_txt(data)

    print("\n[+] Scraping completed successfully.")

    logging.info("Scraping completed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
