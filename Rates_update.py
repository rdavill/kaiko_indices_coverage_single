import requests
import json
import csv
from datetime import datetime, timedelta
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

            for row_num, row in enumerate(reader, start=1):  # Track line numbers
                debug_print(f"Processing row {row_num}: {row}")  # Print full row for debugging

                value = row.get(factsheet_column)  # Safely get the value
                debug_print(f"Row {row_num} - '{factsheet_column}' value: {value}")  # Print the value

                if value and isinstance(value, str) and value.strip():
                    debug_print(f"Found factsheet for ticker {row.get('Ticker', 'Unknown')} at row {row_num}")
                    fact_sheets[row['Ticker']] = value

    debug_print(f"Total factsheets found: {len(fact_sheets)}")
    return fact_sheets

def get_fixed_entries():
    # Fixed entries that should always appear at the top
     return [
        ('Kaiko', 'Blue-Chip', 'Kaiko Eagle Index', 'EGLX', 'N/A', 'N/A', 'NYC Fixing', 'February 11, 2025', 'February 11, 2025', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Eagle Index', 'EGLXRT', 'N/A', 'N/A', 'Real-time (5 sec)', 'February 11, 2025', 'February 11, 2025', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top5 Index', 'KT5', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'March 19, 2018', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top5 Index NYC', 'KT5NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'March 19, 2018', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top5 Index LDN', 'KT5LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'March 19, 2018', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top5 Index SGP', 'KT5SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'March 19, 2018', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top10 Index', 'KT10', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'March 18, 2019', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top10 Index NYC', 'KT10NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'March 18, 2019', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top10 Index LDN', 'KT10LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'March 18, 2019', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top10 Index SGP', 'KT10SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'March 18, 2019', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top15 Index', 'KT15', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'December 23, 2019', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top15 Index NYC', 'KT15NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'December 23, 2019', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top15 Index LDN', 'KT15LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'December 23, 2019', '-', '-'),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top15 Index SGP', 'KT15SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'December 23, 2019', '-', '-'),
        ('Kaiko', 'Thematic', 'Kaiko Tokenization Index', 'KSTKNZ', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'January 3, 2022', '-', '-'),
        ('Kaiko', 'Thematic', 'Kaiko Tokenization Index NYC', 'KSTKNZNYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'January 3, 2022', '-', '-'),
        ('Kaiko', 'Thematic', 'Kaiko Tokenization Index LDN', 'KSTKNZLDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'January 3, 2022', '-', '-'),
        ('Kaiko', 'Thematic', 'Kaiko Tokenization Index SGP', 'KSTKNZSGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'January 3, 2022', '-', '-'),
        ('Kaiko', 'Thematic', 'Kaiko AI Index', 'KSAI', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'October 3, 2022', '-', '-'),
        ('Kaiko', 'Thematic', 'Kaiko AI Index NYC', 'KSAINYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'October 3, 2022', '-', '-'),
        ('Kaiko', 'Thematic', 'Kaiko AI Index LDN', 'KSAILDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'October 3, 2022', '-', '-'),
        ('Kaiko', 'Thematic', 'Kaiko AI Index SGP', 'KSAISGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'October 3, 2022', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko Meme Index', 'KSMEME', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 22, 2025', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko Meme Index NYC', 'KSMEMENYC', 'N/A', 'N/A', 'NYC Fixing', 'January 22, 2025', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko Meme Index LDN', 'KSMEMELDN', 'N/A', 'N/A', 'LDN Fixing', 'January 22, 2025', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko Meme Index SGP', 'KSMEMESGP', 'N/A', 'N/A', 'SGP Fixing', 'January 22, 2025', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko DeFi Index', 'KSDEFI', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 17, 2025', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko DeFi Index NYC', 'KSDEFINYC', 'N/A', 'N/A', 'NYC Fixing', 'January 17, 2025', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko DeFi Index LDN', 'KSDEFILDN', 'N/A', 'N/A', 'LDN Fixing', 'January 17, 2025', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko DeFi Index SGP', 'KSDEFISGP', 'N/A', 'N/A', 'SGP Fixing', 'January 17, 2025', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko L2 Index', 'KSL2', 'N/A', 'N/A', 'Real-time (5 sec)', 'July 2, 2024', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko L2 Index NYC', 'KSL2NYC', 'N/A', 'N/A', 'NYC Fixing', 'July 2, 2024', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko L2 Index LDN', 'KSL2LDN', 'N/A', 'N/A', 'LDN Fixing', 'July 2, 2024', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Sector', 'Kaiko L2 Index SGP', 'KSL2SGP', 'N/A', 'N/A', 'SGP Fixing', 'July 2, 2024', 'April 3, 2023', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Standard Index', 'KMSTA', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'April 1, 2014', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Standard Index NYC', 'KMSTANYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Standard Index LDN', 'KMSTALDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Standard Index SGP', 'KMSTASGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index', 'KMSMA', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'January 2, 2015', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index NYC', 'KMSMANYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'January 2, 2015', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index LDN', 'KMSMALDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'January 2, 2015', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index SGP', 'KMSMASGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'January 2, 2015', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index', 'KMMID', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'April 2, 2018', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index NYC', 'KMMIDNYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'April 2, 2018', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index LDN', 'KMMIDLDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'April 2, 2018', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index SGP', 'KMMIDSGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'April 2, 2018', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index', 'KMLAR', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'April 1, 2014', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index NYC', 'KMLARNYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index LDN', 'KMLARLDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index SGP', 'KMLARSGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Investable Index', 'KMINV', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'April 1, 2014', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Investable Index NYC', 'KMINVNYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Investable Index LDN', 'KMINVLDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-'),
        ('Kaiko', 'Market', 'Kaiko Investable Index SGP', 'KMINVSGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-')
    ]

def fetch_historical_prices_data(ticker, api_key, retries=3, delay=5):
    """Fetch historical price data without time parameters (fetch latest)."""
    debug_print(f"Fetching historical prices data for ticker: {ticker}")

    if not ticker.startswith('KK_') and not ticker.startswith('CBOE-KAIKO_'):
        debug_print(f"Skipping non-reference rate ticker: {ticker}")
        return '-', '-'

    url = f"https://us.marketapi.kaiko.io/v2/data/index.v1/digital_asset_rates_price/{ticker}?parameters=true"
    headers = {'X-API-KEY': api_key, 'Accept': 'application/json'}

    for attempt in range(retries):
        try:
            debug_print(f"Attempt {attempt + 1} - Requesting {url}")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    first_item = data['data'][0]
                    params_data = first_item.get('parameters', {})
                    exchanges = ', '.join(params_data.get('exchanges', [])) or '-'
                    calc_window = str(params_data.get('calc_window', '-'))

                    debug_print(f"Success: {ticker} - Exchanges: {exchanges}, Calculation Window: {calc_window}")
                    return exchanges, calc_window

            debug_print(f"Error fetching {ticker}, status {response.status_code}, retrying in {delay} seconds...")
            time.sleep(delay)

        except requests.exceptions.RequestException as e:
            debug_print(f"RequestException on attempt {attempt + 1}: {e}, retrying in {delay} seconds...")
            time.sleep(delay)

    debug_print(f"Failed after {retries} attempts for {ticker}")
    return '-', '-'

def create_factsheet_only_csv(all_items, headers):
    """Create a separate CSV containing only rows with factsheets"""
    factsheet_items = [item for item in all_items if item[-1].strip()]
    
    debug_print(f"Found {len(factsheet_items)} items with factsheets")
    
    if factsheet_items:
        output_path = "Reference_Rates_With_Factsheets.csv"
        debug_print(f"Creating filtered CSV at: {os.path.abspath(output_path)}")
        
        # For the factsheet CSV, we don't want the Exchanges and Calculation Window columns
        # So we need to create new rows without those columns
        factsheet_csv_items = []
        for item in factsheet_items:
            # Create a new item without the Exchanges and Calculation Window columns
            new_item = item[:9] + (item[-1],)  # Take first 9 columns and the last column (factsheet)
            factsheet_csv_items.append(new_item)
        
        factsheet_headers = [
            'Brand', 'Benchmark Family', 'Name', 'Ticker', 'Base', 'Quote',
            'Dissemination', 'Launch Date', 'Inception Date', 'Factsheet'
        ]
        
        with open(output_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(factsheet_headers)
            writer.writerows(factsheet_csv_items)
        debug_print("Successfully created filtered CSV")

def pull_and_save_data_to_csv(api_url, api_key):
    debug_print("Starting data pull and save process")
    
    existing_fact_sheets = get_existing_fact_sheets()
    fixed_items = get_fixed_entries()
    
    headers = [
        'Brand', 'Benchmark Family', 'Name', 'Ticker', 'Base', 'Quote',
        'Dissemination', 'Launch Date', 'Inception Date', 'Exchanges', 'Calculation Window', 'Factsheet'
    ]
    
    debug_print("Fetching API data...")
    response = requests.get(api_url)
    if response.status_code == 200:
        data = json.loads(response.text)
        api_items = []
        
        for item in data['data']:
            ticker = item['ticker']
            type_value = item['type'].replace('_', ' ')
            
            benchmark_family = type_value
            if type_value == "Reference Rate":
                benchmark_family = "Single asset"
            elif type_value == "Benchmark Reference Rate":
                benchmark_family = "Single asset (BMR compliant)"
            elif type_value == "Custom Rate":
                benchmark_family = "Single asset (Custom)"
            
            brand = item['brand']
            quote_short_name = item['quote']['short_name'].upper()
            base_short_name = item['base']['short_name'].upper()
            short_name = item['short_name'].replace('_', ' ')
            launch_date = parse_date(item['launch_date'])
            inception = parse_date(item['inception_date'])
            dissemination = item['dissemination']
            fact_sheet = existing_fact_sheets.get(ticker, '')
            
            # Fetch exchanges and calculation window data
            exchanges, calc_window = fetch_historical_prices_data(ticker, api_key)
            
            api_items.append((
                brand, benchmark_family, short_name, ticker, base_short_name, quote_short_name,
                dissemination, launch_date, inception, exchanges, calc_window, fact_sheet
            ))
        
        # Add factsheet column to fixed_items (they already have exchanges and calc_window as '-')
        fixed_items_with_fact_sheets = [entry + (existing_fact_sheets.get(entry[3], ''),) for entry in fixed_items]
        all_items = fixed_items_with_fact_sheets + sorted(api_items, key=lambda row: row[5])
        
        debug_print("Saving main CSV...")
        main_csv_path = "Reference_Rates_Coverage.csv"
        with open(main_csv_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(all_items)
        
        debug_print("Creating filtered CSV...")
        create_factsheet_only_csv(all_items, headers)
        debug_print("Process complete")
    else:
        debug_print(f"Error fetching data: {response.status_code}")

debug_print("Starting script execution...")

# Try to get the API key from either environment variable
api_key = os.environ.get('KAIKO_API_KEY') or os.environ.get('API_KEY')

# Check if API key is still missing
if not api_key:
    debug_print("Error: API key is missing! Check your environment variables.")
    sys.exit(1)

# Proceed with the script if API key is found
pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates", api_key)
