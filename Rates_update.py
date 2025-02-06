import requests
import json
import csv
from datetime import datetime
import os
import sys

def debug_print(message):
    """Print debug messages that will show up in GitHub Actions logs"""
    print(f"DEBUG: {message}", file=sys.stderr)

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%B %d, %Y')
    except ValueError:
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')

def get_existing_fact_sheets():
    """Read existing factsheet links from the current CSV"""
    fact_sheets = {}
    csv_path = "Reference_Rates_Coverage.csv"
    debug_print(f"Looking for CSV at: {os.path.abspath(csv_path)}")
    
    if os.path.exists(csv_path):
        debug_print("Found existing CSV file")
        with open(csv_path, "r", newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            factsheet_column = 'Factsheet' if 'Factsheet' in reader.fieldnames else 'Fact Sheet'
            for row in reader:
                if factsheet_column in row and row[factsheet_column].strip():
                    debug_print(f"Found factsheet for ticker {row['Ticker']}")
                    fact_sheets[row['Ticker']] = row[factsheet_column]
    
    debug_print(f"Total factsheets found: {len(fact_sheets)}")
    return fact_sheets

def get_fixed_entries():
    # Updated fixed entries with new Benchmark Family column
    fixed_entries = [
        ('Kaiko', 'Blue-Chip', 'Kaiko Top5 Index', 'KT5', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'March 19, 2018', ''),
        # ... (rest of the fixed entries remain the same, just ensure 10 columns)
    ]
    return fixed_entries

def create_factsheet_only_csv(all_items, headers):
    """Create a separate CSV containing only rows with factsheets"""
    factsheet_items = []
    for item in all_items:
        if item[-1].strip():  # Check if factsheet column is non-empty
            debug_print(f"Including item with factsheet: {item[3]}")
            factsheet_items.append(item)
    
    debug_print(f"Found {len(factsheet_items)} items with factsheets")
    
    if factsheet_items:
        output_path = "Reference_Rates_With_Factsheets.csv"
        debug_print(f"Creating filtered CSV at: {os.path.abspath(output_path)}")
        try:
            with open(output_path, "w", newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headers)
                writer.writerows(factsheet_items)
            debug_print("Successfully created filtered CSV")
            if os.path.exists(output_path):
                debug_print(f"Filtered CSV file exists, size: {os.path.getsize(output_path)} bytes")
            else:
                debug_print("Warning: Filtered CSV file was not created")
        except Exception as e:
            debug_print(f"Error creating filtered CSV: {str(e)}")
    else:
        debug_print("No items with factsheets found - filtered CSV not created")

def pull_and_save_data_to_csv(api_url):
    debug_print("Starting data pull and save process")
    
    # Get existing factsheet links
    existing_fact_sheets = get_existing_fact_sheets()
    
    # Get fixed entries first
    fixed_items = get_fixed_entries()
    
    # Get API data
    debug_print("Fetching API data...")
    response = requests.get(api_url)
    if response.status_code == 200:
        data = json.loads(response.text)
        api_items = []
        for item in data['data']:
            ticker = item['ticker']
            # Skip if the ticker is already in fixed entries
            if any(fixed_item[3] == ticker for fixed_item in fixed_items):
                continue
            
            # Skip if quote is USDT - removed type condition
            if item['quote']['short_name'].upper() == 'USDT':
                continue
            
            # Modify type based on new requirements
            orig_type = item['type'].replace('_', ' ')
            if orig_type == 'Reference Rate':
                benchmark_family = 'Single-asset'
            elif orig_type == 'Benchmark Reference Rate':
                benchmark_family = 'Single-asset (BMR-compliant)'
            else:
                benchmark_family = orig_type.replace('_', ' ')
            
            brand = item['brand']
            quote_short_name = item['quote']['short_name'].upper()
            base_short_name = item['base']['short_name'].upper()
            short_name = item['short_name'].replace('_', ' ')
            launch_date = parse_date(item['launch_date'])
            inception = parse_date(item['inception_date'])
            dissemination = item['dissemination']
            
            # Get existing factsheet link or empty string
            fact_sheet = existing_fact_sheets.get(ticker, '')
            if fact_sheet:
                debug_print(f"Adding factsheet for {ticker}")
            
            # Reorder columns according to new specification
            api_items.append((
                brand,              # Brand
                benchmark_family,   # Benchmark Family (modified type)
                short_name,         # Name
                ticker,             # Ticker
                base_short_name,    # Base
                quote_short_name,   # Quote
                dissemination,      # Dissemination
                launch_date,        # Launch Date
                inception,          # Inception Date
                fact_sheet          # Factsheet
            ))
        
        # Add factsheets to fixed entries
        fixed_items_with_fact_sheets = [
            entry + (existing_fact_sheets.get(entry[3], ''),) for entry in fixed_items
        ]
        
        # Combine fixed and API items
        all_items = fixed_items_with_fact_sheets + sorted(api_items, key=lambda row: row[5])  # Sort by Quote
        
        # Updated headers to match new column order and rename 'Type' to 'Benchmark Family'
        headers = [
            'Brand', 'Benchmark Family', 'Name', 'Ticker', 'Base', 'Quote',
            'Dissemination', 'Launch Date', 'Inception Date', 'Factsheet'
        ]
        
        debug_print("Saving main CSV...")
        main_csv_path = "Reference_Rates_Coverage.csv"
        with open(main_csv_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(all_items)
        
        debug_print("Creating filtered CSV...")
        create_factsheet_only_csv(all_items, headers)
        debug_print("Process complete")
        
        # List directory contents for debugging
        debug_print("Current directory contents:")
        debug_print("\n".join(os.listdir(".")))
    else:
        debug_print(f"Error fetching data: {response.status_code}")

# Call the function with the API URL
debug_print("Starting script execution...")
pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates")
