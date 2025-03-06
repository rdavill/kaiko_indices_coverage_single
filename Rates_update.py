import requests
import json
import csv
import os
import sys
from datetime import datetime

def debug_print(message):
    """Print debug messages that will show up in GitHub Actions logs."""
    print(f"DEBUG: {message}", file=sys.stderr)

def parse_date(date_string):
    """Convert API date format to readable format."""
    try:
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%B %d, %Y')
    except ValueError:
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')

def get_normalized_family(family_type):
    """
    Normalize the benchmark family according to desired grouping:
    - Thematic -> "Sector & Thematic"
    - Sector -> "Sector & Thematic"
    - Custom_Rate -> "Single-Asset"
    - Benchmark_Reference_Rate -> "Single-Asset"
    - Reference_Rate -> "Single-Asset"
    """
    if family_type in ["Thematic", "Sector"]:
        return "Sector & Thematic"
    elif family_type in ["Custom_Rate", "Benchmark_Reference_Rate", "Reference_Rate"]:
        return "Single-Asset"
    else:
        return family_type

def get_existing_fact_sheets():
    """Read existing factsheet links from the current CSV."""
    fact_sheets = {}
    csv_path = "Reference_Rates_Coverage.csv"
    debug_print(f"Looking for CSV at: {os.path.abspath(csv_path)}")

    if os.path.exists(csv_path):
        debug_print("Found existing CSV file")
        with open(csv_path, "r", newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            factsheet_column = 'Factsheet' if 'Factsheet' in reader.fieldnames else 'Fact Sheet'

            for row_num, row in enumerate(reader, start=1):  # Track line numbers
                if factsheet_column in row:
                    value = row.get(factsheet_column, "").strip()
                    # Remove any trailing commas from factsheet values
                    if value.endswith(','):
                        value = value[:-1]
                    
                    if value:
                        ticker = row.get('Ticker', 'Unknown')
                        debug_print(f"Found factsheet for ticker {ticker} at row {row_num}")
                        
                        # Fix double href tags if present
                        if '<a href="<a href="' in value:
                            value = value.replace('<a href="<a href="', '<a href="')
                        
                        fact_sheets[ticker] = value

    debug_print(f"Total factsheets found: {len(fact_sheets)}")
    return fact_sheets

def get_fixed_entries():
    """Return a list of fixed index entries that should always be included."""
    factsheet_blue_chip = '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/New%20Benchmark%20Factsheets/Kaiko%20Benchmarks%20-%20Blue-Chip%20family%20factsheet.pdf" target="_blank">View Factsheet</a>'
    factsheet_sector_thematic = '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/New%20Benchmark%20Factsheets/Kaiko%20Benchmarks%20-%20Sector%20&%20Thematic%20family%20factsheet.pdf" target="_blank">View Factsheet</a>'
    factsheet_market = '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/New%20Benchmark%20Factsheets/Kaiko%20Benchmarks%20-%20Market%20family%20factsheet.pdf" target="_blank">View Factsheet</a>'

    # Expanded list to include all 54 records
    return [
        # Blue-Chip Indices with Expanded Location-Based Variants
        ('Kaiko', 'Blue-Chip', 'Kaiko Eagle Index', 'EGLX', 'N/A', 'N/A', 'NYC Fixing', 'February 11, 2025', 'February 11, 2025', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Eagle Index', 'EGLXRT', 'N/A', 'N/A', 'Real-time (5 sec)', 'February 11, 2025', 'February 11, 2025', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top5 Index', 'KT5', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'March 19, 2018', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top5 Index NYC', 'KT5NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'March 19, 2018', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top5 Index LDN', 'KT5LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'March 19, 2018', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top5 Index SGP', 'KT5SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'March 19, 2018', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top10 Index', 'KT10', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'March 18, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top10 Index NYC', 'KT10NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'March 18, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top10 Index LDN', 'KT10LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'March 18, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top10 Index SGP', 'KT10SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'March 18, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top15 Index', 'KT15', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'December 23, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top15 Index NYC', 'KT15NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'December 23, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top15 Index LDN', 'KT15LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'December 23, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Top15 Index SGP', 'KT15SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'December 23, 2019', '-', '-', factsheet_blue_chip),

        # Thematic Indices with Location-Based Variants - Change 'Thematic' to 'Sector & Thematic'
        ('Kaiko', 'Sector & Thematic', 'Kaiko Tokenization Index', 'KSTKNZ', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'January 3, 2022', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Tokenization Index NYC', 'KSTKNZNYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'January 3, 2022', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Tokenization Index LDN', 'KSTKNZLDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'January 3, 2022', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Tokenization Index SGP', 'KSTKNZSGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'January 3, 2022', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko AI Index', 'KSAI', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'October 3, 2022', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko AI Index NYC', 'KSAINYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'October 3, 2022', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko AI Index LDN', 'KSAILDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'October 3, 2022', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko AI Index SGP', 'KSAISGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'October 3, 2022', '-', '-', factsheet_sector_thematic),

        # Sector Indices with Location-Based Variants - Change 'Sector' to 'Sector & Thematic'
        ('Kaiko', 'Sector & Thematic', 'Kaiko Meme Index', 'KSMEME', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 22, 2025', 'April 3, 2023', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Meme Index NYC', 'KSMEMENYC', 'N/A', 'N/A', 'NYC Fixing', 'January 22, 2025', 'April 3, 2023', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Meme Index LDN', 'KSMEMELDN', 'N/A', 'N/A', 'LDN Fixing', 'January 22, 2025', 'April 3, 2023', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Meme Index SGP', 'KSMEMESGP', 'N/A', 'N/A', 'SGP Fixing', 'January 22, 2025', 'April 3, 2023', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko DeFi Index', 'KSDEFI', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 17, 2025', 'April 3, 2023', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko DeFi Index NYC', 'KSDEFINYC', 'N/A', 'N/A', 'NYC Fixing', 'January 17, 2025', 'April 3, 2023', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko DeFi Index LDN', 'KSDEFILDN', 'N/A', 'N/A', 'LDN Fixing', 'January 17, 2025', 'April 3, 2023', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko DeFi Index SGP', 'KSDEFISGP', 'N/A', 'N/A', 'SGP Fixing', 'January 17, 2025', 'April 3, 2023', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko L2 Index', 'KSL2', 'N/A', 'N/A', 'Real-time (5 sec)', 'July 2, 2024', 'April 3, 2023', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko L2 Index NYC', 'KSL2NYC', 'N/A', 'N/A', 'NYC Fixing', 'July 2, 2024', 'April 3, 2023', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko L2 Index LDN', 'KSL2LDN', 'N/A', 'N/A', 'LDN Fixing', 'July 2, 2024', 'April 3, 2023', '-', '-', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko L2 Index SGP', 'KSL2SGP', 'N/A', 'N/A', 'SGP Fixing', 'July 2, 2024', 'April 3, 2023', '-', '-', factsheet_sector_thematic),

        # Market Indices with Location-Based Variants
        ('Kaiko', 'Market', 'Kaiko Standard Index', 'KMSTA', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Standard Index NYC', 'KMSTANYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Standard Index LDN', 'KMSTALDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Standard Index SGP', 'KMSTASGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index', 'KMSMA', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'January 2, 2015', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index NYC', 'KMSMANYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'January 2, 2015', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index LDN', 'KMSMALDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'January 2, 2015', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index SGP', 'KMSMASGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'January 2, 2015', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index', 'KMMID', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'April 2, 2018', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index NYC', 'KMMIDNYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'April 2, 2018', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index LDN', 'KMMIDLDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'April 2, 2018', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index SGP', 'KMMIDSGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'April 2, 2018', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index', 'KMLAR', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index NYC', 'KMLARNYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index LDN', 'KMLARLDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index SGP', 'KMLARSGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Investable Index', 'KMINV', 'N/A', 'N/A', 'Real-time (5 sec)', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Investable Index NYC', 'KMINVNYC', 'N/A', 'N/A', 'NYC Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Investable Index LDN', 'KMINVLDN', 'N/A', 'N/A', 'LDN Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Investable Index SGP', 'KMINVSGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market)
    ]

def fetch_historical_prices_data(ticker, asset_type, api_key):
    """Fetch historical price data only for Reference_Rate and Benchmark_Reference_Rate."""
    debug_print(f"Fetching historical prices data for ticker: {ticker}, Type: {asset_type}")

    # If no API key provided, return default values
    if not api_key:
        debug_print(f"No API key provided, skipping historical data fetch for {ticker}")
        return '-', '-'

    # ✅ Only process 'Reference_Rate' and 'Benchmark_Reference_Rate'
    if asset_type not in ['Reference_Rate', 'Benchmark_Reference_Rate', 'Single-Asset']:
        debug_print(f"Skipping ticker {ticker} (type: {asset_type}) - Not a reference rate.")
        return '-', '-'

    url = f"https://us.market-api.kaiko.io/v2/data/index.v1/digital_asset_rates_price/{ticker}?parameters=true"
    headers = {'X-API-KEY': api_key, 'Accept': 'application/json'}

    try:
        debug_print(f"Making API request to: {url}")
        response = requests.get(url, headers=headers, timeout=10)

        debug_print(f"Response Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            debug_print(f"Response JSON: {json.dumps(data, indent=2)[:500]}")  # Print first 500 characters

            if 'data' in data and data['data']:
                first_item = data['data'][0]
                params_data = first_item.get('parameters', {})
                exchanges = ', '.join(params_data.get('exchanges', [])) or '-'
                calc_window = str(params_data.get('calc_window', '-'))

                debug_print(f"✅ Success: {ticker} - Exchanges: {exchanges}, Calculation Window: {calc_window}")
                return exchanges, calc_window
            else:
                debug_print(f"⚠️ No 'data' key or empty response for ticker: {ticker}")

        debug_print(f"❌ API call failed with status {response.status_code}: {response.text}")
        return '-', '-'

    except requests.exceptions.RequestException as e:
        debug_print(f"🚨 RequestException: {e}")
        return '-', '-'

def write_filtered_csv(items, headers):
    """Write a filtered CSV with only the entries that have factsheets."""
    filtered_csv_path = "Reference_Rates_With_Factsheets.csv"
    filtered_headers = headers[:10] + [headers[-1]]  # Keep all headers except Exchanges and Calculation Window
    
    # Filter items that have factsheets
    filtered_items = []
    for item in items:
        if item[-1] and item[-1] != '-' and item[-1] != '':
            # Take only the columns we need (exclude Exchanges and Calculation Window)
            # Convert to list first to avoid tuple/list concatenation issue
            item_list = list(item)
            filtered_item = item_list[:10] + [item_list[-1]]
            filtered_items.append(filtered_item)
    
    debug_print(f"Writing filtered CSV with {len(filtered_items)} entries")
    
    with open(filtered_csv_path, "w", newline='') as csv_file:
        writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(filtered_headers)
        writer.writerows(filtered_items)
    
    debug_print(f"Filtered CSV saved to {filtered_csv_path}")
    
    # Log the families for debugging
    families = set(item[1] for item in items)
    debug_print(f"Benchmark families in the data: {families}")

def pull_and_save_data_to_csv(api_url, api_key):
    """Fetch reference rates and save them to CSV."""
    debug_print("Starting data pull and save process")

    existing_fact_sheets = get_existing_fact_sheets()
    fixed_items = get_fixed_entries()

    headers = [
        'Brand', 'Benchmark Family', 'Name', 'Ticker', 'Base', 'Quote',
        'Dissemination', 'Launch Date', 'Inception Date', 'Exchanges', 'Calculation Window', 'Factsheet'
    ]

    # Use the URL as-is since it already includes the quote=usd filter
    debug_print(f"Fetching API data from: {api_url}")
    
    # Don't need API key for reference data
    response = requests.get(api_url)

    if response.status_code == 200:
        data = json.loads(response.text)
        api_items = []

        for item in data['data']:
            ticker = item['ticker']
            asset_type = item['type']  # ✅ Check type instead of guessing
            # Normalize the benchmark family
            normalized_family = get_normalized_family(asset_type)
            
            brand = item['brand']
            quote_short_name = item['quote']['short_name'].upper()
            base_short_name = item['base']['short_name'].upper()
            short_name = item['short_name'].replace('_', ' ')
            launch_date = parse_date(item['launch_date'])
            inception = parse_date(item['inception_date'])
            dissemination = item['dissemination']
            
            # Get factsheet from existing data or use empty string (not dash)
            fact_sheet = existing_fact_sheets.get(ticker, '')
            
            # Remove any trailing commas from factsheet
            if fact_sheet.endswith(','):
                fact_sheet = fact_sheet[:-1]

            # ✅ Fetch exchanges & calculation window - this part still needs the API key
            exchanges, calc_window = fetch_historical_prices_data(ticker, asset_type, api_key)

            api_items.append((
                brand, normalized_family, short_name, ticker, base_short_name, quote_short_name,
                dissemination, launch_date, inception, exchanges, calc_window, fact_sheet
            ))

        # Process fixed items - already normalized in get_fixed_entries
        fixed_items_with_fact_sheets = []
        for entry in fixed_items:
            ticker = entry[3]
            # Use either the factsheet from fixed data or from existing CSV, with no trailing comma
            factsheet = entry[11]
            if ticker in existing_fact_sheets and existing_fact_sheets[ticker]:
                factsheet = existing_fact_sheets[ticker]
                if factsheet.endswith(','):
                    factsheet = factsheet[:-1]
            
            fixed_items_with_fact_sheets.append(entry[:11] + (factsheet,))
        
        all_items = fixed_items_with_fact_sheets + sorted(api_items, key=lambda row: row[3])

        # ✅ Save to CSV
        main_csv_path = "Reference_Rates_Coverage.csv"
        debug_print(f"Saving main CSV to {os.path.abspath(main_csv_path)}")

        with open(main_csv_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)
            writer.writerows(all_items)
        
        # Write the filtered CSV with only entries that have factsheets
        write_filtered_csv(all_items, headers)

        debug_print("Process complete")
    else:
        debug_print(f"❌ Error fetching API data: {response.status_code}")

# 🚀 Main Execution
if __name__ == "__main__":
    debug_print("Starting script execution...")

    # ✅ Retrieve API key from environment - only needed for historical prices data
    api_key = os.environ.get('KAIKO_API_KEY') or os.environ.get('API_KEY')
    if not api_key:
        debug_print("⚠️ Warning: API key is missing! Exchanges and Calculation Window columns will show '-'.")
        api_key = ""  # Use empty string instead of None to avoid errors
    
    # URL with quote=usd parameter already included
    pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates?quote=usd", api_key)
