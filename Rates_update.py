import requests
import json
import csv
from datetime import datetime
import os

def parse_date(date_string):
    try:
        # Try parsing with milliseconds
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%B %d, %Y')
    except ValueError:
        # If that fails, try without milliseconds
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')

def get_existing_fact_sheets():
    """Read existing fact sheet links from the current CSV"""
    fact_sheets = {}
    if os.path.exists("Reference_Rates_Coverage.csv"):
        with open("Reference_Rates_Coverage.csv", "r", newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if 'Fact Sheet' in row and row['Fact Sheet']:  # Only store non-empty fact sheet links
                    fact_sheets[row['Ticker']] = row['Fact Sheet']
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

def pull_and_save_data_to_csv(api_url):
    # Get existing fact sheet links
    existing_fact_sheets = get_existing_fact_sheets()
    
    # Get fixed entries first
    fixed_items = get_fixed_entries()
    
    # Get API data
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
        
        with open("Reference_Rates_Coverage.csv", "w", newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(all_items)
    else:
        print(f"Error fetching data: {response.status_code}")

# Call the function with the API URL
pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates")
