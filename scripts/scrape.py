# built-in imports
import re
import os
import time
from json import dump
from tqdm import tqdm
from collections import defaultdict
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

# constants
BASE_URL = "https://www.domain.com.au"
N_PAGES = range(1, 3)  # update this to your liking
OUTPUT_FILE = '../data/raw/example.json'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# function to fetch URLs of property listings
def fetch_property_links(pages):
    url_links = []
    for page in pages:
        url = BASE_URL + f"/rent/melbourne-region-vic/?sort=price-desc&page={page}"
        print(f"Visiting {url}")
        try:
            bs_object = BeautifulSoup(urlopen(Request(url, headers=HEADERS)), "lxml")
            index_links = bs_object.find("ul", {"data-testid": "results"}).findAll(
                "a", href=re.compile(f"{BASE_URL}/*")
            )
            for link in index_links:
                if 'address' in link.get('class', []):
                    url_links.append(link['href'])
        except Exception as e:
            print(f"Error fetching {url}: {e}")
    return url_links

# function to scrape metadata from each property page
def scrape_property_data(url_links):
    property_metadata = defaultdict(dict)
    success_count, total_count = 0, 0
    pbar = tqdm(url_links)
    for property_url in pbar:
        try:
            bs_object = BeautifulSoup(urlopen(Request(property_url, headers=HEADERS)), "lxml")
            total_count += 1

            property_metadata[property_url]['name'] = bs_object.find("h1", {"class": "css-164r41r"}).text
            property_metadata[property_url]['cost_text'] = bs_object.find("div", {"data-testid": "listing-details__summary-title"}).text

            rooms = bs_object.find("div", {"data-testid": "property-features"}).findAll("span", {"data-testid": "property-features-text-container"})
            property_metadata[property_url]['rooms'] = [re.findall(r'\d+\s[A-Za-z]+', feature.text)[0] for feature in rooms if 'Bed' in feature.text or 'Bath' in feature.text]
            property_metadata[property_url]['parking'] = [re.findall(r'\S+\s[A-Za-z]+', feature.text)[0] for feature in rooms if 'Parking' in feature.text]

            desc_element = bs_object.find("p")
            property_metadata[property_url]['desc'] = re.sub(r'<br\/>', '\n', str(desc_element)).strip('</p>') if desc_element else ''

            success_count += 1
        except Exception as e:
            print(f"Issue with {property_url}: {e}")

        pbar.set_description(f"{(success_count/total_count * 100):.0f}% successful")
        time.sleep(1)  # add delay to reduce load on server
    return property_metadata

# function to save data to a JSON file
def save_data(data, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        dump(data, f)

# main execution
if __name__ == "__main__":
    links = fetch_property_links(N_PAGES)
    metadata = scrape_property_data(links)
    save_data(metadata, OUTPUT_FILE)

