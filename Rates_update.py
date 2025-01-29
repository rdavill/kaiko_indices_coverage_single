import requests
import json
import csv
from datetime import datetime
import os

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
                if 'Fact Sheet' in row and row['Fact Sheet'].strip():  # Check for non-empty fact sheets
                    print(f"Found fact sheet for ticker {row['Ticker']}: {row['Fact Sheet']}")
                    fact_sheets[row['Ticker']] = row['Fact Sheet']
    print(f"Total fact sheets found: {len(fact_sheets)}")
    return fact_sheets

def get_fixed_entries():
    # Fixed entries that should always appear at the top
    return [
        ('KT5', 'Kaiko', 'INDEX', 'INDEX', 'Blue-Chip', 'Real-time (5 sec)', 'Kaiko Top5 Index', 'October 17, 2023', 'March 19, 2018'),
        # ... [rest of fixed entries remain the same]
    ]

def create_factsheet_only_csv(all_items, headers):
    """Create a separate CSV containing only rows with fact sheets"""
    # Filter for rows that have a fact sheet (last column is not empty)
    factsheet_items = [item for item in all_items if item[-1].strip()]
    print(f"Found {len(factsheet_items)} items with fact sheets for filtered CSV")
    
    if factsheet_items:
        print("Creating filtered CSV with fact sheet items...")
        with open("Reference_Rates_With_Factsheets.csv", "w", newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(factsheet_items)
        print(f"Created filtered CSV with {len(factsheet_items)} rows")
    else:
        print("No items with fact sheets found - filtered CSV not created")

def pull_and_save_data_to_csv(api_url):
    # Get existing fact sheet links
    print("Reading existing fact sheets...")
    existing_fact_sheets = get_existing_fact_sheets()
    
    # Get fixed entries first
    fixed_items = get_fixed_entries()
    
    # Get API data
    print("Fetching API data...")
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
                print(f"Adding fact sheet for {ticker}")
            
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
        
        print("Saving main CSV...")
        # Save main CSV with all data
        with open("Reference_Rates_Coverage.csv", "w", newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(all_items)
        
        print("Creating filtered CSV...")
        # Create additional CSV with only fact sheet rows
        create_factsheet_only_csv(all_items, headers)
        print("Process complete")
    else:
        print(f"Error fetching data: {response.status_code}")

# Call the function with the API URL
print("Starting script execution...")
pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates")
