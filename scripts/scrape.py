import re
import os
import time
import random
import csv
from tqdm import tqdm
from collections import defaultdict
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup

# constants
BASE_URL = "https://www.domain.com.au"
SUBURBS = ['ashburton-vic-3147']
''', 'balwyn-north-vic-3104','balwyn-vic-3103', 'camberwell-vic-3124', 'glen-iris-vic-3146', 'hawthorn-east-vic-3123',
           'kew-east-vic-3102', 'surrey-hills-vic-3127', 'hawthorn-vic-3122', 'kew-vic-3101', 'bulleen-vic-3105', 'doncaster-vic-3108',
           'templestowe-vic-3106', 'templestowe-lower-vic-3107','doncaster-east-vic-3109','blackburn-vic-3130','blackburn-south-vic-3130','blackburn-north-vic-3130',
           'box-hill-vic-3128','box-hill-south-vic-3128','box-hill-north-vic-3129','burwood-vic-3125','burwood-east-vic-3151','mont-albert-vic-3127'''
N_PAGES = range(1, 15)  
OUTPUT_FILE = 'data/landing/rental_scrape.csv'


def fetch_property_links(pages, suburbs):
    """
    Fetches URLs of property listings from a specified number of pages.

    Parameters:
    pages: a range of pages to scrape for property links.

    Returns:
    list: A list of URLs pointing to individual property listings.
    """
    print("Starting to fetch property links...")
    url_links = []
    for suburb in suburbs:
        for page in pages:
            url = BASE_URL + f"/rent/{suburb}/?page={page}"
            print(f"Visiting {url}")
            try:
                print("Sending request to server...")
                bs_object = BeautifulSoup(urlopen(Request(url, headers={'User-Agent':"PostmanRuntime/7.6.0"}), timeout=100), "lxml")
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
            delay = random.uniform(1, 2)
            print(f"Delaying for {delay:.2f} seconds...")
            time.sleep(delay)
    print("Finished fetching property links.")
    return url_links

def get_unique_urls(url_list):
    """
    Filters out duplicate URLs from the list.

    Parameters:
    url_list: A list of URLs.

    Returns:
    list: A list of unique URLs.
    """
    url_list = list(set(url_list))
    print(f"Filtered unique URLs. Original count: {len(url_list)}, Unique count: {len(url_list)}")
    return url_list

def scrape_property_data(url_links):
    """
    Scrapes basic metadata from each property listing page.

    Parameters:
    url_links: a list of URLs pointing to individual property listings.

    Returns:
    defaultdict: a dictionary containing scraped metadata for each property.
    """
    print("Starting to scrape property data...")
    all_properties = []
    success_count, total_count = 0, 0
    pbar = tqdm(url_links)
    for property_url in pbar:
        retry_count = 0
        max_retries = 3
        backoff_time = 1  
    
        while retry_count < max_retries:
            print(f"Scraping {property_url} (Attempt {retry_count + 1}/{max_retries})")
            try:
                bs_object = BeautifulSoup(urlopen(Request(property_url, headers={'User-Agent': "PostmanRuntime/7.6.0"}), timeout=303), "lxml")
                total_count += 1

                # Extract property details
                name = bs_object.find("h1", {"class": "css-164r41r"}).text if bs_object.find("h1", {"class": "css-164r41r"}) else 'N/A'
                cost_text = bs_object.find("div", {"data-testid": "listing-details__summary-title"}).text if bs_object.find("div", {"data-testid": "listing-details__summary-title"}) else 'N/A'
                rooms = bs_object.find("div", {"data-testid": "property-features"}).findAll("span", {"data-testid": "property-features-text-container"})
                bed_info = [re.findall(r'\d+\s[A-Za-z]+', feature.text)[0] for feature in rooms if 'Bed' in feature.text]
                bath_info = [re.findall(r'\d+\s[A-Za-z]+', feature.text)[0] for feature in rooms if 'Bath' in feature.text]
                parking_info = [re.findall(r'\S+\s[A-Za-z]+', feature.text)[0] for feature in rooms if 'Parking' in feature.text]
                desc_element = bs_object.find("p")
                desc = re.sub(r'<br\/>', '\n', str(desc_element)).strip('</p>') if desc_element else 'N/A'
                address_element = bs_object.find("span", {"class": "css-class-for-address"})
                address = address_element.text if address_element else 'Address not found'
                property_type_element = bs_object.find("div", {"data-testid":"listing-summary-property-type"})
                property_type = property_type_element.find("span").text.strip() if property_type_element else 'N/A'

                # Collect data
                # Collect data
                all_properties.append({
                    'URL': property_url,
                    'Name': name,
                    'Cost': cost_text,
                    'Bedrooms': ', '.join(bed_info),
                    'Bathrooms': ', '.join(bath_info),
                    'Parking': ', '.join(parking_info),
                    'Description': desc,
                    'Address': address,
                    'PropertyType': property_type
                })

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
    return all_properties


def save_data(data, output_file):
    """
    Saves scraped property metadata to a CSV file.

    Parameters:
    data: list of dictionaries containing property metadata to save.
    output_file: the path where the CSV file will be saved.
    """
    try:
        print(f"Saving data to {output_file}...")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Define CSV headers
        headers = ['URL', 'Name', 'Cost', 'Bedrooms', 'Bathrooms', 'Parking', 'Description', 'Address', 'PropertyType']

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)

        print(f"Data successfully saved to {output_file}.")
    
    except Exception as e:
        print(f"An error occurred while saving data: {e}")

# main execution
if __name__ == "__main__":
    links = fetch_property_links(N_PAGES, SUBURBS)
    links = get_unique_urls(links)
    metadata = scrape_property_data(links)
    save_data(metadata, OUTPUT_FILE)


