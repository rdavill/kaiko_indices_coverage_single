import requests
import json
import csv
from datetime import datetime
import os
import logging

# Set up logging to write to a file
logging.basicConfig(
    filename='rates_script.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%B %d, %Y')
    except ValueError:
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')

def get_existing_fact_sheets():
    """Read existing fact sheet links from the current CSV"""
    fact_sheets = {}
    if os.path.exists("Reference_Rates_Coverage.csv"):
        with open("Reference_Rates_Coverage.csv", "r", newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if 'Fact Sheet' in row and row['Fact Sheet'].strip():
                    logging.info(f"Found fact sheet for ticker {row['Ticker']}: {row['Fact Sheet']}")
                    fact_sheets[row['Ticker']] = row['Fact Sheet']
    logging.info(f"Total fact sheets found: {len(fact_sheets)}")
    return fact_sheets

def get_fixed_entries():
    # Fixed entries that should always appear at the top
    fixed_entries = [
        ('KT5', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'Real-time (5 sec)', 'Kaiko Top5 Index', 'October 17, 2023', 'March 19, 2018'),
        ('KT5NYC', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'NYC Fixing', 'Kaiko Top5 Index NYC', 'October 17, 2023', 'March 19, 2018'),
        ('KT5LDN', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'LDN Fixing', 'Kaiko Top5 Index LDN', 'October 17, 2023', 'March 19, 2018'),
        ('KT5SGP', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'SGP Fixing', 'Kaiko Top5 Index SGP', 'October 17, 2023', 'March 19, 2018'),
        ('KT10', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'Real-time (5 sec)', 'Kaiko Top10 Index', 'October 17, 2023', 'March 18, 2019'),
        ('KT10NYC', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'NYC Fixing', 'Kaiko Top10 Index NYC', 'October 17, 2023', 'March 18, 2019'),
        ('KT10LDN', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'LDN Fixing', 'Kaiko Top10 Index LDN', 'October 17, 2023', 'March 18, 2019'),
        ('KT10SGP', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'SGP Fixing', 'Kaiko Top10 Index SGP', 'October 17, 2023', 'March 18, 2019'),
        ('KT15', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'Real-time (5 sec)', 'Kaiko Top15 Index', 'October 17, 2023', 'December 23, 2019'),
        ('KT15NYC', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'NYC Fixing', 'Kaiko Top15 Index NYC', 'October 17, 2023', 'December 23, 2019'),
        ('KT15LDN', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'LDN Fixing', 'Kaiko Top15 Index LDN', 'October 17, 2023', 'December 23, 2019'),
        ('KT15SGP', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'SGP Fixing', 'Kaiko Top15 Index SGP', 'October 17, 2023', 'December 23, 2019')
    ]
    return fixed_entries

def create_factsheet_only_csv(all_items, headers):
    """Create a separate CSV containing only rows with fact sheets"""
    # Debug the content we're working with
    logging.info(f"Total items to check: {len(all_items)}")
    
    # Filter for rows that have a fact sheet (last column is not empty)
    factsheet_items = []
    for item in all_items:
        if item[-1].strip():  # Check if last column (fact sheet) is non-empty
            logging.info(f"Found item with fact sheet: {item[0]}")  # Log ticker of item with fact sheet
            factsheet_items.append(item)
    
    logging.info(f"Found {len(factsheet_items)} items with fact sheets for filtered CSV")
    
    if factsheet_items:
        logging.info("Creating filtered CSV with fact sheet items...")
        try:
            with open("Reference_Rates_With_Factsheets.csv", "w", newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headers)
                writer.writerows(factsheet_items)
            logging.info(f"Successfully created filtered CSV with {len(factsheet_items)} rows")
        except Exception as e:
            logging.error(f"Error creating filtered CSV: {str(e)}")
    else:
        logging.warning("No items with fact sheets found - filtered CSV not created")

def pull_and_save_data_to_csv(api_url):
    logging.info("Starting data pull and save process")
    
    # Get existing fact sheet links
    existing_fact_sheets = get_existing_fact_sheets()
    
    # Get fixed entries first
    fixed_items = get_fixed_entries()
    
    # Get API data
    logging.info("Fetching API data...")
    response = requests.get(api_url)
    if response.status_code == 200:
        data = json.loads(response.text)
        api_items = []
        for item in data['data']:
            ticker = item['ticker']
            # Skip if the ticker is already in fixed entries
            if any(fixed_item[0] == ticker for fixed_item in fixed_items):
                continue
                
            brand = item['brand']
            quote_short_name = item['quote']['short_name'].upper()
            base_short_name = item['base']['short_name'].upper()
            type = item['type'].replace('_', ' ')
            dissemination = item['dissemination']
            short_name = item['short_name'].replace('_', ' ')
            launch_date = parse_date(item['launch_date'])
            inception = parse_date(item['inception_date'])
            
            # Get existing fact sheet link or empty string
            fact_sheet = existing_fact_sheets.get(ticker, '')
            if fact_sheet:
                logging.info(f"Adding fact sheet for {ticker}")
            
            api_items.append((ticker, brand, quote_short_name, base_short_name, type, 
                            dissemination, short_name, launch_date, inception, fact_sheet))
        
        # Add fact sheets to fixed entries
        fixed_items_with_fact_sheets = [
            entry + (existing_fact_sheets.get(entry[0], ''),) for entry in fixed_items
        ]
        
        # Combine fixed and API items
        all_items = fixed_items_with_fact_sheets + sorted(api_items, key=lambda row: row[3])
        
        headers = ['Ticker', 'Brand', 'Quote (short name)', 'Base (short name)', 
                  'Type', 'Dissemination', 'Rate Short name', 'Launch Date', 
                  'Inception', 'Fact Sheet']
        
        logging.info("Saving main CSV...")
        # Save main CSV with all data
        with open("Reference_Rates_Coverage.csv", "w", newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(all_items)
        
        logging.info("Creating filtered CSV...")
        # Create additional CSV with only fact sheet rows
        create_factsheet_only_csv(all_items, headers)
        logging.info("Process complete")
    else:
        logging.error(f"Error fetching data: {response.status_code}")

# Call the function with the API URL
logging.info("Starting script execution...")
pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates")
