import re
import os
import time
import random
from json import dump
from tqdm import tqdm
from collections import defaultdict
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# constants
BASE_URL = "https://www.domain.com.au"
N_PAGES = range(1, 50)  
OUTPUT_FILE = 'data/raw/rental_scrape.json'

# initalizing fake user agent
ua = UserAgent()

def get_random_headers():
    """
    Generates a random headers dictionary with a rotating user-agent.
    
    Returns:
    dict: A dictionary containing HTTP headers with a random user-agent.
    """
    headers = {'User-Agent': ua.random}
    print(f"Using User-Agent: {headers['User-Agent']}")
    return headers

def fetch_property_links(pages):
    """
    Fetches URLs of property listings from a specified number of pages.

    Parameters:
    pages: a range of pages to scrape for property links.

    Returns:
    list: A list of URLs pointing to individual property listings.
    """
    print("Starting to fetch property links...")
    url_links = []
    for page in pages:
        url = BASE_URL + f"/rent/melbourne-region-vic/?sort=price-desc&page={page}"
        print(f"Visiting {url}")
        try:
            print("Sending request to server...")
            bs_object = BeautifulSoup(urlopen(Request(url, headers=headers), timeout=100), "lxml")
            print("Successfully received response.")
            index_links = bs_object.find("ul", {"data-testid": "results"}).findAll(
                "a", href=re.compile(f"{BASE_URL}/*")
            )
            for link in index_links:
                if 'address' in link.get('class', []):
                    url_links.append(link['href'])
                    print(f"Found link: {link['href']}")
        except HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
        except URLError as e:
            print(f"URL Error: {e.reason}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        # Add random delay between requests
        delay = random.uniform(1, 3)
        print(f"Delaying for {delay:.2f} seconds...")
        time.sleep(delay)
    print("Finished fetching property links.")
    return url_links

def scrape_property_data(url_links):
    """
    Scrapes basic metadata from each property listing page.

    Parameters:
    url_links: a list of URLs pointing to individual property listings.

    Returns:
    defaultdict: a dictionary containing scraped metadata for each property.
    """
    print("Starting to scrape property data...")
    property_metadata = defaultdict(dict)
    success_count, total_count = 0, 0
    pbar = tqdm(url_links)
    for property_url in pbar:
        retry_count = 0
        max_retries = 3
        backoff_time = 1  # Start with 1 second backoff
        
        while retry_count < max_retries:
            print(f"Scraping {property_url} (Attempt {retry_count + 1}/{max_retries})")
            try:
                headers = get_random_headers()
                bs_object = BeautifulSoup(urlopen(Request(property_url, headers=headers)), "lxml")
                total_count += 1

                # finding property name
                property_metadata[property_url]['name'] = bs_object.find("h1", {"class": "css-164r41r"}).text
                
                # finding cost
                property_metadata[property_url]['cost_text'] = bs_object.find("div", {"data-testid": "listing-details__summary-title"}).text
                
                # finding rooms and parking info
                rooms = bs_object.find("div", {"data-testid": "property-features"}).findAll("span", {"data-testid": "property-features-text-container"})
                property_metadata[property_url]['rooms'] = [re.findall(r'\d+\s[A-Za-z]+', feature.text)[0] for feature in rooms if 'Bed' in feature.text or 'Bath' in feature.text]
                property_metadata[property_url]['parking'] = [re.findall(r'\S+\s[A-Za-z]+', feature.text)[0] for feature in rooms if 'Parking' in feature.text]
                
                # finding description
                desc_element = bs_object.find("p")
                property_metadata[property_url]['desc'] = re.sub(r'<br\/>', '\n', str(desc_element)).strip('</p>') if desc_element else ''

                # finding address
                address_element = bs_object.find("span", {"class": "css-class-for-address"})  # Adjust based on actual class/id
                property_metadata[property_url]['address'] = address_element.text if address_element else 'Address not found'

                print(f"Successfully scraped data for {property_url}")
                success_count += 1
                break  
            except Exception as e:
                print(f"Issue with {property_url}: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)  
                    backoff_time *= 2  # backing off on retry
                else:
                    print(f"Failed to scrape {property_url} after {max_retries} attempts.")
                    
        pbar.set_description(f"{(success_count/total_count * 100):.0f}% successful")
    
    print("Finished scraping property data.")
    return property_metadata

def is_json_file_empty(file_path):
    """
    Checks if a JSON file is empty.

    Parameters: 
    file_path: the path to the JSON file.

    Returns:
    bool: True if the file is empty or only contains whitespace, otherwise False.
    """

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read().strip()  
            return len(content) == 0  
    else:
        print("File does not exist.")
        return True  

def save_data(data, output_file):
    """
    Saves scraped property metadata to a JSON file.

    Parameters:
    data: dict containing property metadata to save.
    output_file: the path where the JSON file will be saved.
    """
    try:
        print(f"Saving data to {output_file}...")

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w') as f:
            dump(data, f)

        print(f"Data successfully save to {output_file}.")

        #checking if empty
        if is_json_file_empty(output_file):
            print(f"Warning: The JSON file at {output_file} is empty.")
        else:
            print(f"The JSON file at {output_file} is not empty.")
    
    except Exception as e:
        print(f"An error occurred while saving data: {e}")

# main execution
if __name__ == "__main__":
    links = fetch_property_links(N_PAGES)
    metadata = scrape_property_data(links)
    save_data(metadata, OUTPUT_FILE)


