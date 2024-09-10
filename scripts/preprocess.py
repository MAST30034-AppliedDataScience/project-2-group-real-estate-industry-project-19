import pandas as pd
import re
from dateutil import parser
from datetime import datetime
suburb_postcode_mapping = {
    'ashburton': '3147', 'balwyn north': '3104', 'balwyn': '3103', 'camberwell': '3124', 'glen iris': '3146', 
    'hawthorn-east': '3123', 'kew east': '3102', 'surrey hills': '3127', 'hawthorn': '3122', 'kew': '3101', 
    'bulleen': '3105', 'doncaster': '3108', 'templestowe': '3106', 'templestowe lower': '3107', 
    'doncaster east': '3109', 'blackburn': '3130', 'blackburn south': '3130', 'blackburn north': '3130',
    'box hill': '3128', 'box hill south': '3128', 'box hill north': '3129', 'burwood': '3125', 
    'burwood east': '3151', 'mont albert': '3127'
}

def extract_suburb_postcode(address):
    '''This function outputs the suburb and postcode based on the address
    
    Parameters:
    address: address string that contains the suburb
    
    Returns:
    suburb and postcode
    '''
    address_lower = address.lower() 
    for suburb, postcode in suburb_postcode_mapping.items():
        if suburb in address_lower:
            return suburb.title(), postcode
    return 'Unknown', 'Unknown'


def categorise_property(row):
    '''
    This function categorizes properties based on the structure of the address.
    
    Parameters:
    row: instance in the dataset
    
    Returns:
    property type
    '''
     # If 'Property Type' is NaN or missing, categorize based on the address
    if pd.isna(row['Property Type']):
        # Extract the first part of the address (number part) using split
        number_part = row['Address'].split(' ')[0]

        # Check if the number part is 'UNIT' or contains any '/' or letters
        if number_part.upper() == 'UNIT' or re.search(r'[/A-Za-z]', number_part):
            return 'Apartment / Unit / Flat'
        else:
            return 'House'
    
    # If the property is already categorized as 'Townhouse', keep it as 'Townhouse'
    if 'Townhouse' in row['Property Type']:
        return 'Townhouse'

    # If not a townhouse, check for unit/apartment or house based on the address
    number_part = row['Address'].split(' ')[0]
    if number_part.upper() == 'UNIT' or re.search(r'[/A-Za-z]', number_part):
        return 'Apartment / Unit / Flat'
    else:
        return 'House'
    
def calculate_annual_increase(row):
    historical_prices = row['Historical Prices']
    
    if pd.isna(historical_prices):
        return pd.Series([None, None, None, None])  # Return None for all outputs if no historical prices
    
    # Use regex to extract date-price pairs like 'August 2023$1,100'
    date_price_pairs = re.findall(r'([A-Za-z]+\s\d{4})\$([\d,]+)(?:\s*-\s*\$[\d,]*)?', historical_prices)
    
    # Convert extracted data to usable format
    if not date_price_pairs:
        return pd.Series([None, None, None, None])
    
    # Parse the dates and prices
    dates_prices = [(parser.parse(date), float(price.replace(',', ''))) for date, price in date_price_pairs]
    
    # Sort by date
    dates_prices.sort(key=lambda x: x[0])
    
    # Extract oldest and newest prices
    oldest_date, oldest_price = dates_prices[0]
    newest_date, newest_price = dates_prices[-1]
    
    # Calculate the number of months between the oldest and newest dates
    months_diff = (newest_date.year - oldest_date.year) * 12 + (newest_date.month - oldest_date.month)
    
    # Calculate the annual increase percentage
    if months_diff == 0:
        annual_increase_pct = None  # Avoid division by zero if the dates are the same
    else:
        annual_increase_pct = ((newest_price - oldest_price) / oldest_price) * (12 / months_diff) * 100
    
    return pd.Series([oldest_price, oldest_date, newest_price, newest_date, months_diff, annual_increase_pct])

def extract_number(value):
    ''''This function extracts the number from a string
    
    Parameters:
    value: instance from a feature that contains the feature and number eg '1 Bed
    
    Returns:
    numbers: just the number from the instance'''
    if pd.isna(value):
        return None  # Keep NaN as is
    # Use regex to find all numeric characters and join them into a single number
    numbers = re.findall(r'\d+', str(value))
    return int(numbers[0]) if numbers else None

def extract_first_number(cost):
    '''This function find the rental price from a string
    
    Parameters:
    cost: string with rental price inside
    
    Returns:
    math: just the rental price'''
    if pd.isna(cost):
        return None  # Keep NaN as is
    # Use regex to find the first occurrence of a number (with optional decimal)
    match = re.search(r'\d+[\.,]?\d*', str(cost))
    if match:
        # Return the matched number as a float after removing any commas
        return float(match.group(0).replace(',', ''))
    return None