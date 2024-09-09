import requests
from bs4 import BeautifulSoup
import csv
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


N_PAGES = range(1,50)
BASE_URL = "https://www.oldlistings.com.au/real-estate/VIC/"
SUBURBS = [
    'Ashburton/3147', 'Balwyn+North/3104', 'Balwyn/3103', 'Camberwell/3124', 
    'Glen+Iris/3146', 'Hawthorn+East/3123', 'Kew+East/3102', 'Surrey+Hills/3127', 
    'Hawthorn/3122', 'Kew/3101'
]
SUBURBS2 = ['Bulleen/3105', 'Doncaster/3108', 
    'Templestowe/3106', 'Templestowe+Lower/3107', 'Doncaster+East/3109',
    'Blackburn/3130', 'Blackburn+South/3130', 'Blackburn+North/3130',
    'Box+Hill/3128', 'Box+Hill+South/3128', 'Box+Hill+North/3129',
    'Burwood/3125', 'Burwood+East/3151', 'Mont+Albert/3127']


def test_urls(pages, suburbs):
    """
    Tests the URLs of property listings to check if they are accessible.

    Parameters:
    pages: a range of pages to test.
    suburbs: a list of suburb URLs to test.

    Returns:
    list: A list of accessible URLs.
    """
    print("Starting to test property URLs...")
    accessible_urls = []

    # Loop through each suburb and page number
    for suburb in suburbs:
        for page in pages:
            url = f"{BASE_URL}{suburb}/rent/{page}"
            print(f"Visiting {url}")
            try:
                print("Sending request to server...")
                response = requests.get(url, headers={'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}, timeout=10)
                
                # Check if the request was successful
                if response.status_code == 200:
                    print(f"Successfully received response for {url}.")
                    accessible_urls.append(url)
                else:
                    print(f"Received status code {response.status_code} for {url}.")
            
            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error for {url}: {e}")
            except requests.exceptions.RequestException as e:
                print(f"Request Exception for {url}: {e}")
            
            # Add a random delay between requests
            delay = random.uniform(1, 2)
            print(f"Delaying for {delay:.2f} seconds...")
            time.sleep(delay)
    
    print("Finished testing property URLs.")
    return accessible_urls


def scrape_oldlistings_data(urls):
    """
    Scrapes property data from a list of URLs on oldlistings.com.au.

    Parameters:
    urls: list of str, URLs to scrape data from.

    Returns:
    list: A list of dictionaries containing scraped property data.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    all_properties = []
    
    print("Starting to scrape property data...")
    success_count, total_count = 0, 0
    pbar = tqdm(urls, desc="Scraping URLs", unit="url")
    
    for property_url in pbar:
        retry_count = 0
        max_retries = 3
        backoff_time = 1  # Start with 1 second backoff

        while retry_count < max_retries:
            print(f"Scraping {property_url} (Attempt {retry_count + 1}/{max_retries})")
            try:
                response = requests.get(property_url, headers=headers, timeout=30)
                response.raise_for_status()  # Raise an error for bad responses
                soup = BeautifulSoup(response.text, 'html.parser')
                total_count += 1

                # Find all property listings on the page
                property_listings = soup.find_all('div', class_='property')  # Adjust the class to match the actual HTML

                for listing in property_listings:
                    # Extract property address
                    address = listing.find('h2', class_='address').text.strip() if listing.find('h2', class_='address') else 'Address not found'

                    # Extract room information (bedrooms, bathrooms, car spaces)
                    beds = listing.find('p', class_='property-meta bed').text.strip() if listing.find('p', class_='property-meta bed') else 'N/A'
                    baths = listing.find('p', class_='property-meta bath').text.strip() if listing.find('p', class_='property-meta bath') else 'N/A'
                    cars = listing.find('p', class_='property-meta car').text.strip() if listing.find('p', class_='property-meta car') else 'N/A'
                    property_type = listing.find('p', class_='property-meta type').text.strip() if listing.find('p', class_='property-meta type') else 'N/A'               

                    # Extract historical prices
                    historical_prices = []
                    historical_price_section = listing.find('section', class_='grid-100 historical-price')

                    if historical_price_section:
                        historical_price_tags = historical_price_section.find_all('li')
                        for tag in historical_price_tags:
                            historical_prices.append(tag.text.strip())

                    # Add data to property dictionary
                    all_properties.append({
                        'Address': address,
                        'Beds': beds,
                        'Baths': baths,
                        'Cars': cars,
                        'Property Type': property_type,
                        'Historical Prices': '; '.join(historical_prices)
                    })

                    print(f"Scraped property: {address}")

                success_count += 1
                break  
            except Exception as e:
                print(f"Issue with {property_url}: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)
                    backoff_time *= 2  # Exponential backoff
                else:
                    print(f"Failed to scrape {property_url} after {max_retries} attempts.")
                    
        pbar.set_description(f"{(success_count/total_count * 100):.0f}% successful")

    print("Finished scraping property data.")
    return all_properties

def save_data_to_csv(data, filename):
    """
    Saves the scraped data to a CSV file.

    Parameters:
    data: list of dictionaries containing the property data.
    filename: str, The filename to save the CSV data to.
    """
    try:
        print(f"Saving data to {filename}...")
        # Define CSV headers
        headers = ['Address', 'Beds', 'Baths', 'Cars', 'Property Type', 'Last Advertised Price', 'Historical Prices']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Data successfully saved to {filename}.")
    except Exception as e:
        print(f"Error saving data to CSV: {e}")


# Test the scraping on the specified URL
urls = test_urls(N_PAGES, SUBURBS)
property_data = scrape_oldlistings_data(urls)
save_data_to_csv(property_data, 'data/landing/rental_history_scrape1.csv')
urls = test_urls(N_PAGES, SUBURBS2)
property_data = scrape_oldlistings_data(urls)
save_data_to_csv(property_data, 'data/landing/rental_history_scrape2.csv')