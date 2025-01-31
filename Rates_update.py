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

def process_quote_base(quote_name, base_name, type_value):
    """Process quote and base names based on type"""
    type_value = type_value.lower()
    if type_value in ['blue-chip', 'thematic', 'sector', 'market']:
        quote_name = 'N/A' if quote_name.upper() == 'INDEX' else quote_name
        base_name = 'N/A' if base_name.upper() == 'INDEX' else base_name
    return quote_name, base_name

def get_fixed_entries():
    # Fixed entries that should always appear at the top
    # Order: Brand, Type, Name, Ticker, Base, Quote, Dissemination, Launch Date, Inception
    fixed_entries = [
        # Blue-Chip Indices
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index', 'KT5', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'March 19, 2018'),
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index NYC', 'KT5NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'March 19, 2018'),
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index LDN', 'KT5LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'March 19, 2018'),
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index SGP', 'KT5SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'March 19, 2018'),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index', 'KT10', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'March 18, 2019'),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index NYC', 'KT10NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'March 18, 2019'),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index LDN', 'KT10LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'March 18, 2019'),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index SGP', 'KT10SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'March 18, 2019'),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index', 'KT15', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'December 23, 2019'),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index NYC', 'KT15NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'December 23, 2019'),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index LDN', 'KT15LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'December 23, 2019'),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index SGP', 'KT15SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'December 23, 2019'),
        # Thematic Indices
        ('Kaiko', 'Thematic', 'Kaiko Tokenization Index', 'KSTKNZ', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'January 3, 2022'),
        ('Kaiko', 'Thematic', 'Kaiko Tokenization Index NYC', 'KSTKNZNYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'January 3, 2022'),
        ('Kaiko', 'Thematic', 'Kaiko Tokenization Index LDN', 'KSTKNZLDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'January 3, 2022'),
        ('Kaiko', 'Thematic', 'Kaiko Tokenization Index SGP', 'KSTKNZSGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'January 3, 2022'),
        ('Kaiko', 'Thematic', 'Kaiko AI Index', 'KSAI', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'October 3, 2022'),
        ('Kaiko', 'Thematic', 'Kaiko AI Index NYC', 'KSAINYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'October 3, 2022'),
        ('Kaiko', 'Thematic', 'Kaiko AI Index LDN', 'KSAILDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'October 3, 2022'),
        ('Kaiko', 'Thematic', 'Kaiko AI Index SGP', 'KSAISGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'October 3, 2022'),
        # Sector Indices
        ('Kaiko', 'Sector', 'Kaiko Meme Index', 'KSMEME', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 22, 2025', 'April 3, 2023'),
        ('Kaiko', 'Sector', 'Kaiko Meme Index NYC', 'KSMEMENYC', 'N/A', 'N/A', 'NYC Fixing', 'January 22, 2025', 'April 3, 2023'),
        ('Kaiko', 'Sector', 'Kaiko Meme Index LDN', 'KSMEMELDN', 'N/A', 'N/A', 'LDN Fixing', 'January 22, 2025', 'April 3, 2023'),
        ('Kaiko', 'Sector', 'Kaiko Meme Index SGP', 'KSMEMESGP', 'N/A', 'N/A', 'SGP Fixing', 'January 22, 2025', 'April 3, 2023'),
        ('Kaiko', 'Sector', 'Kaiko DeFi Index', 'KSDEFI', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 17, 2025', 'April 3, 2023'),
        ('Kaiko', 'Sector', 'Kaiko DeFi Index NYC', 'KSDEFINYC', 'N/A', 'N/A', 'NYC Fixing', 'January 17, 2025', 'April 3, 2023'),
        ('Kaiko', 'Sector', 'Kaiko DeFi Index LDN', 'KSDEFILDN', 'N/A', 'N/A', 'LDN Fixing', 'January 17, 2025', 'April 3, 2023'),
        ('Kaiko', 'Sector', 'Kaiko DeFi Index SGP', 'KSDEFISGP', 'N/A', 'N/A', 'SGP Fixing', 'January 17, 2025', 'April 3, 2023'),
        ('Kaiko', 'Sector', 'Kaiko L2 Index', 'KSL2', 'N/A', 'N/A', 'Real-time (5 sec)', 'July 2, 2024', 'April 3, 2023'),
        ('Kaiko', 'Sector', 'Kaiko L2 Index NYC', 'KSL2NYC', 'N/A', 'N/A', 'NYC Fixing', 'July 2, 2024', 'April 3, 2023'),
        ('Kaiko', 'Sector', 'Kaiko L2 Index LDN', 'KSL2LDN', 'N/A', 'N/A', 'LDN Fixing', 'July 2, 2024', 'April 3, 2023'),
        ('Kaiko', 'Sector', 'Kaiko L2 Index SGP', 'KSL2SGP', 'N/A', 'N/A', 'SGP Fixing', 'July 2, 2024', 'April 3, 2023'),
        # Market Indices
        ('Kaiko', 'Market', 'Kaiko Standard Index', 'KMSTA', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'April 1, 2014'),
        ('Kaiko', 'Market', 'Kaiko Standard Index NYC', 'KMSTANYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'April 1, 2014'),
        ('Kaiko', 'Market', 'Kaiko Standard Index LDN', 'KMSTALDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'April 1, 2014'),
        ('Kaiko', 'Market', 'Kaiko Standard Index SGP', 'KMSTASGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'April 1, 2014'),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index', 'KMSMA', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'January 2, 2015'),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index NYC', 'KMSMANYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'January 2, 2015'),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index LDN', 'KMSMALDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'January 2, 2015'),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index SGP', 'KMSMASGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'January 2, 2015'),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index', 'KMMID', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23

def create_factsheet_only_csv(all_items, headers):
    """Create a separate CSV containing only rows with factsheets"""
    factsheet_items = [item for item in all_items if item[-1].strip()]
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
    existing_fact_sheets = get_existing_fact_sheets()
    fixed_items = get_fixed_entries()
    
    debug_print("Fetching API data...")
    response = requests.get(api_url)
    if response.status_code == 200:
        data = json.loads(response.text)
        api_items = []
        for item in data['data']:
            # Skip if quote is USDT
            if item['quote']['short_name'].upper() == 'USDT':
                debug_print(f"Skipping {item['ticker']} - USDT quote")
                continue
                
            ticker = item['ticker']
            # Skip if the ticker is already in fixed entries
            if any(fixed_item[3] == ticker for fixed_item in fixed_items):  # Updated index to match new order
                continue
            
            brand = item['brand']
            quote_short_name = item['quote']['short_name'].upper()
            base_short_name = item['base']['short_name'].upper()
            type_value = item['type'].replace('_', ' ')
            
            # Process quote and base names
            quote_short_name, base_short_name = process_quote_base(
                quote_short_name, base_short_name, type_value
            )
            
            dissemination = item['dissemination']
            short_name = item['short_name'].replace('_', ' ')
            launch_date = parse_date(item['launch_date'])
            inception = parse_date(item['inception_date'])
            fact_sheet = existing_fact_sheets.get(ticker, '')
            
            if fact_sheet:
                debug_print(f"Adding factsheet for {ticker}")
            
            # Order: Brand, Type, Name, Ticker, Base, Quote, Dissemination, Launch Date, Inception, Factsheet
            api_items.append((brand, type_value, short_name, ticker, base_short_name, 
                            quote_short_name, dissemination, launch_date, inception, fact_sheet))
        
        # Add factsheets to fixed entries
        fixed_items_with_fact_sheets = [
            entry + (existing_fact_sheets.get(entry[3], ''),) for entry in fixed_items  # Updated index to match new order
        ]
        
        # Combine fixed and API items
        all_items = fixed_items_with_fact_sheets + sorted(api_items, key=lambda row: row[2])  # Sort by Name
        
        headers = ['Brand', 'Type', 'Name', 'Ticker', 'Base (short name)', 
                  'Quote (short name)', 'Dissemination', 'Launch Date', 
                  'Inception', 'Factsheet']
        
        debug_print("Saving main CSV...")
        main_csv_path = "Reference_Rates_Coverage.csv"
        with open(main_csv_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(all_items)
        
        debug_print("Creating filtered CSV...")
        create_factsheet_only_csv(all_items, headers)
        debug_print("Process complete")
        
        debug_print("Current directory contents:")
        debug_print("\n".join(os.listdir(".")))
    else:
        debug_print(f"Error fetching data: {response.status_code}")

# Call the function with the API URL
debug_print("Starting script execution...")
pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates")
