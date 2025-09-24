import requests
import json
import csv
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict

def debug_print(message):
    """Print debug messages that will show up in GitHub Actions logs."""
    print(f"DEBUG: {message}", file=sys.stderr)

def parse_date(date_string):
    """Convert API date format to readable format."""
    try:
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%B %d, %Y')
    except ValueError:
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')

def get_base_ticker(ticker):
    """Extract base ticker from location-based variants and remove trailing underscores."""
    # Remove trailing underscores first
    cleaned_ticker = ticker.rstrip('_')
    
    # Remove location suffixes
    for suffix in ['NYC', 'LDN', 'SGP']:
        if cleaned_ticker.endswith(suffix):
            return cleaned_ticker[:-len(suffix)]
    return cleaned_ticker

def clean_name(name):
    """Remove location suffixes from name."""
    # Remove location suffixes from the end of names
    for suffix in [' NYC', ' LDN', ' SGP']:
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name

def get_exchange_name_mappings():
    """
    Fetch exchange codes and names from the reference API and create a mapping.
    Returns a dictionary with exchange codes as keys and exchange names as values.
    """
    debug_print("Fetching exchange name mappings from reference API")
    url = "https://reference-data-api.kaiko.io/v1/exchanges"
    
    try:
        debug_print(f"Making GET request to: {url}")
        response = requests.get(url, timeout=15)
        
        debug_print(f"Exchange API response status code: {response.status_code}")
        
        if response.status_code != 200:
            debug_print(f"❌ Failed to fetch exchange mappings: {response.status_code}")
            debug_print(f"Response content: {response.text[:200]}...")
            return {}
            
        response_json = response.json()
        
        # Check for proper response structure
        if "result" not in response_json or response_json["result"] != "success":
            debug_print(f"❌ API returned unsuccessful result: {response_json.get('result', 'N/A')}")
            return {}
            
        # Access the "data" field which contains the exchange list
        if "data" not in response_json or not isinstance(response_json["data"], list):
            debug_print(f"❌ API response missing 'data' field or not a list: {list(response_json.keys())}")
            return {}
            
        exchange_list = response_json["data"]
        debug_print(f"Exchange API response contains {len(exchange_list)} exchanges")
        
        # Sample some data for debugging
        if len(exchange_list) > 0:
            debug_print(f"Sample exchange data: {exchange_list[0:2]}")
        
        # Create mapping of code -> name
        mappings = {}
        for exchange in exchange_list:
            if 'code' in exchange and 'name' in exchange:
                code = exchange['code'].lower()  # Normalize to lowercase
                name = exchange['name']
                
                # Special case for CRCO
                if code == 'crco':
                    mappings[code] = 'Crypto.com'
                else:
                    mappings[code] = name
        
        debug_print(f"✅ Successfully created {len(mappings)} exchange mappings")
        
        # Print some sample mappings for debugging
        sample_keys = list(mappings.keys())[:5] if len(mappings) > 5 else list(mappings.keys())
        for key in sample_keys:
            debug_print(f"Sample mapping: {key} -> {mappings[key]}")
        
        # Check specifically for common exchange codes
        common_codes = ["cbse", "krkn", "crco", "stmp", "lmax", "itbi"]
        for code in common_codes:
            if code in mappings:
                debug_print(f"✅ Found mapping for common exchange: {code} -> {mappings[code]}")
            else:
                debug_print(f"⚠️ Missing mapping for common exchange: {code}")
            
        return mappings
        
    except Exception as e:
        debug_print(f"❌ Error fetching exchange mappings: {str(e)}")
        return {}

def fetch_historical_prices_data(ticker, asset_type, api_key, exchange_mappings=None):
    """
    Fetch historical price data for Reference_Rate, Benchmark_Reference_Rate, and Single-Asset.
    Uses exchange_mappings to convert exchange codes to full names.
    Filters out rates with publication time before 9pm UTC yesterday.
    """
    debug_print(f"Fetching historical prices data for ticker: {ticker}, Type: {asset_type}")
    
    # Calculate 9pm UTC yesterday
    yesterday_9pm_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    yesterday_9pm_utc = yesterday_9pm_utc.replace(hour=21)  # 9pm UTC
    debug_print(f"Filtering cutoff time: {yesterday_9pm_utc.isoformat()}Z")
    
    # Load exchange mappings if not provided or if empty
    if exchange_mappings is None or len(exchange_mappings) == 0:
        debug_print("Exchange mappings missing or empty, generating new mappings")
        exchange_mappings = get_exchange_name_mappings()
        debug_print(f"Generated {len(exchange_mappings)} exchange mappings")
    else:
        debug_print(f"Using provided exchange mappings with {len(exchange_mappings)} items")
    
    # If no API key provided, return default values
    if not api_key:
        debug_print(f"No API key provided, skipping historical data fetch for {ticker}")
        return '-'
    
    # Only process single-asset types
    if asset_type not in ['Reference_Rate', 'Benchmark_Reference_Rate', 'Custom_Rate']:
        debug_print(f"Skipping ticker {ticker} (type: {asset_type}) - Not a single-asset rate.")
        return '-'
    
    # Build URL with page_size=1, sort=desc and parameters=true
    url = f"https://us.market-api.kaiko.io/v2/data/index.v1/digital_asset_rates_price/{ticker}?page_size=1&parameters=true&sort=desc"
    
    headers = {'X-Api-Key': api_key, 'Accept': 'application/json'}
    
    try:
        debug_print(f"Making API request to: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        debug_print(f"Response Status Code: {response.status_code}")
        if response.status_code != 200:
            debug_print(f"❌ API call failed with status {response.status_code}: {response.text}")
            return '-'
            
        data = response.json()
        
        # Check the publication time and filter if before 9pm UTC yesterday
        if 'time' in data:
            try:
                # Parse the time field
                publication_time = datetime.strptime(data['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
                debug_print(f"Publication time for {ticker}: {publication_time.isoformat()}Z")
                
                if publication_time < yesterday_9pm_utc:
                    debug_print(f"🚫 Excluding {ticker} - publication time {publication_time.isoformat()}Z is before cutoff {yesterday_9pm_utc.isoformat()}Z")
                    return 'EXCLUDE'  # Special return value to indicate exclusion
                    
            except ValueError as e:
                debug_print(f"⚠️ Could not parse time field for {ticker}: {data.get('time', 'N/A')} - {e}")
        else:
            debug_print(f"⚠️ No 'time' field found in response for {ticker}")
        
        # Check if we have data
        if not data.get('data') or len(data['data']) == 0:
            debug_print(f"⚠️ No data found for ticker: {ticker}")
            return '-'
        
        # Get the first interval (should be the most recent one due to sort=desc)
        first_interval = data['data'][0]
        
        # Extract exchanges from parameters
        exchanges = '-'
        
        if 'parameters' in first_interval:
            params = first_interval['parameters']
            
            # Get exchanges
            if 'exchanges' in params and params['exchanges']:
                exchanges_list = params['exchanges']
                debug_print(f"Found exchange codes for {ticker}: {exchanges_list}")
                
                # Map exchange codes to full names using our mappings
                mapped_exchanges = []
                for exchange_code in sorted(exchanges_list):
                    # Normalize to lowercase for consistent lookup
                    exchange_code_lower = exchange_code.lower()
                    
                    # Map exchange code to full name
                    if exchange_code_lower in exchange_mappings:
                        mapped_name = exchange_mappings[exchange_code_lower]
                        mapped_exchanges.append(mapped_name)
                        debug_print(f"Mapped exchange code {exchange_code} to {mapped_name}")
                    else:
                        # If no mapping exists, use the code as is
                        mapped_exchanges.append(exchange_code)
                        debug_print(f"⚠️ No mapping found for exchange code: {exchange_code}")
                
                exchanges = ', '.join(mapped_exchanges)
                debug_print(f"Final mapped exchanges for {ticker}: {exchanges}")
            else:
                debug_print(f"No exchanges found in parameters for {ticker}")
        else:
            debug_print(f"No parameters found in response for {ticker}")
        
        debug_print(f"✅ Success: {ticker} - Exchanges: {exchanges}")
        return exchanges
        
    except requests.exceptions.RequestException as e:
        debug_print(f"🚨 RequestException: {e}")
        return '-'
    except Exception as e:
        debug_print(f"🚨 Unexpected error processing {ticker}: {str(e)}")
        return '-'

def merge_location_variants(items):
    """Merge location-based variants into single rows with combined disseminations, preserving original order."""
    debug_print("Starting merge of location variants for single assets")
    
    # Use OrderedDict to preserve insertion order
    ticker_groups = OrderedDict()
    ticker_order = []  # Track the order in which base tickers first appear
    
    for item in items:
        original_ticker = item[3]  # Original ticker is at index 3
        base_ticker = get_base_ticker(original_ticker)
        
        if base_ticker not in ticker_groups:
            ticker_groups[base_ticker] = []
            ticker_order.append(base_ticker)
        
        ticker_groups[base_ticker].append(item)
    
    merged_items = []
    
    # Process in the original order
    for base_ticker in ticker_order:
        variants = ticker_groups[base_ticker]
        debug_print(f"Processing base ticker: {base_ticker} with {len(variants)} variants")
        
        # Find the base variant (without location suffix)
        base_variant = None
        location_variants = []
        
        for variant in variants:
            original_ticker = variant[3]
            cleaned_ticker = original_ticker.rstrip('_')
            if get_base_ticker(original_ticker) == base_ticker and not any(cleaned_ticker.endswith(suffix) for suffix in ['NYC', 'LDN', 'SGP']):
                base_variant = variant
            else:
                location_variants.append(variant)
        
        if base_variant is None:
            # If no base variant found, use the first one as base
            base_variant = variants[0]
            location_variants = variants[1:]
        
        # Build disseminations string
        disseminations = [base_variant[6]]  # Start with base dissemination (index 6)
        
        # Add location disseminations in order: NYC, LDN, SGP
        locations_found = []
        for location in ['NYC', 'LDN', 'SGP']:
            for variant in location_variants:
                original_ticker = variant[3]
                cleaned_ticker = original_ticker.rstrip('_')
                if cleaned_ticker.endswith(location):
                    locations_found.append(location)
                    break
        
        if locations_found:
            disseminations.extend(locations_found)
        
        combined_disseminations = ', '.join(disseminations)
        
        # Clean the name by removing location suffixes
        cleaned_name = clean_name(base_variant[2])
        
        # Ensure base_ticker has no trailing underscores
        clean_base_ticker = base_ticker.rstrip('_')
        
        # Create merged entry using base variant's data
        merged_entry = (
            base_variant[0],  # Brand
            base_variant[1],  # Type (raw, no normalization)
            cleaned_name,     # Cleaned name (no location suffixes)
            clean_base_ticker,  # Use cleaned base ticker
            base_variant[4],  # Base
            base_variant[5],  # Quote
            combined_disseminations,  # Combined disseminations
            base_variant[7],  # Launch Date
            base_variant[8],  # Inception Date
            base_variant[9],  # Exchanges
            base_variant[10]  # Learn more link (previously Rulebook)
        )
        
        merged_items.append(merged_entry)
        debug_print(f"Merged {clean_base_ticker}: {cleaned_name} -> {combined_disseminations}")
    
    debug_print(f"Merged {len(items)} items into {len(merged_items)} entries")
    return merged_items

def pull_and_save_data_to_csv(api_url, api_key):
    """Fetch single-asset reference rates and save them to CSV, excluding entries with Coinbase in exchanges."""
    debug_print("Starting data pull and save process for single-asset rates")
    
    # Get exchange name mappings upfront to reuse for all API calls
    exchange_mappings = get_exchange_name_mappings()
    debug_print(f"Loaded {len(exchange_mappings)} exchange mappings for all API calls")
    
    # Debug output the mappings for common exchange codes
    common_codes = ["cbse", "krkn", "crco", "stmp", "lmax", "itbi"]
    for code in common_codes:
        if code in exchange_mappings:
            debug_print(f"✓ Main mapping for {code}: {exchange_mappings[code]}")
        else:
            debug_print(f"✗ Missing mapping for {code}")
    
    # Headers for single-asset rates (Type instead of Benchmark Family) - Changed 'Rulebook' to 'Learn more'
    headers = [
        'Brand', 'Type', 'Name', 'Ticker', 'Base', 'Quote',
        'Dissemination(s)', 'Launch Date', 'Inception Date', 'Exchanges', 'Learn more'
    ]
    
    # Fetch API data
    debug_print(f"Fetching API data from: {api_url}")
    
    response = requests.get(api_url)
    if response.status_code == 200:
        data = json.loads(response.text)
        api_items = []
        
        # Log item types for debugging
        item_types = {}
        for item in data['data']:
            item_type = item.get('type', 'Unknown')
            item_types[item_type] = item_types.get(item_type, 0) + 1
        
        debug_print(f"Item types in API response: {item_types}")
        
        # Filter for USD quote items only
        usd_items = []
        for item in data['data']:
            quote_short_name = item['quote']['short_name'].upper()
            if quote_short_name == 'USD':
                usd_items.append(item)
        
        debug_print(f"Filtered {len(data['data'])} items to {len(usd_items)} USD quote items")
        
        # Count of single-asset types after filtering
        single_asset_count = 0
        
        for item in usd_items:
            ticker = item['ticker']
            asset_type = item['type']
            
            # Filter out Custom_Rate types
            if asset_type == 'Custom_Rate':
                debug_print(f"Excluding {ticker} - type is Custom Rate")
                continue
            
            # Only process single-asset types (excluding Custom_Rate)
            if asset_type not in ['Reference_Rate', 'Benchmark_Reference_Rate']:
                continue
            
            single_asset_count += 1
            
            # Use raw type data but remove underscores
            type_display = asset_type.replace('_', ' ')
            
            brand = item['brand']
            quote_short_name = item['quote']['short_name'].upper()
            base_short_name = item['base']['short_name'].upper()
            short_name = item['short_name'].replace('_', ' ')
            launch_date = parse_date(item['launch_date'])
            inception = parse_date(item['inception_date'])
            dissemination = item['dissemination']
            
            # Fetch exchanges using the exchange mappings
            exchanges = fetch_historical_prices_data(ticker, asset_type, api_key, exchange_mappings)
            
            # Skip if excluded due to time filtering
            if exchanges == 'EXCLUDE':
                debug_print(f"Excluding {ticker} due to time filtering")
                continue
            
            # Create 'Learn more' link for all rows
            learn_more_link = f'<a href="https://explorer.kaiko.com/rates/{ticker}" target="_blank">explore performance</a>'
            
            api_items.append((
                brand, type_display, short_name, ticker, base_short_name, quote_short_name,
                dissemination, launch_date, inception, exchanges, learn_more_link
            ))
        
        debug_print(f"Found {single_asset_count} single-asset items after USD filtering")
        debug_print(f"Processing {len(api_items)} items after time filtering")
        
        # Merge location variants
        merged_items = merge_location_variants(api_items)
        
        # Filter out items with Coinbase in exchanges before saving
        filtered_items = []
        coinbase_count = 0
        for item in merged_items:
            exchanges_column = item[9]  # Exchanges is the 10th column (index 9)
            if "Coinbase" not in exchanges_column:
                filtered_items.append(item)
            else:
                coinbase_count += 1
                debug_print(f"Excluding {item[3]} due to Coinbase in exchanges: {exchanges_column}")
        
        debug_print(f"Filtered from {len(merged_items)} to {len(filtered_items)} items (removed {coinbase_count} Coinbase entries)")
        
        # Check for items with non-default exchanges
        non_default_count = sum(1 for item in filtered_items if item[9] != '-')
        debug_print(f"Items with non-default exchanges: {non_default_count}")
        
        # Save to CSV with filtered items
        main_csv_path = "Reference_Rates_Coverage.csv"
        debug_print(f"Saving main CSV to {os.path.abspath(main_csv_path)}")
        with open(main_csv_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)
            writer.writerows(filtered_items)
        
        debug_print("Process complete")
        
    else:
        debug_print(f"❌ Error fetching API data: {response.status_code}")

# Main execution
if __name__ == "__main__":
    debug_print("Starting script execution...")
    debug_print("Repository: https://github.com/rdavill/kaiko_indices_coverage_single")
    debug_print("Processing single-asset rates only")
    
    # Retrieve API key from environment or set directly
    api_key = os.environ.get("KAIKO_API_KEY", "")
    
    if not api_key or api_key == "your_actual_api_key_here":
        debug_print("⚠️ Warning: API key is missing! Please set your actual API key.")
        api_key = ""
    else:
        debug_print(f"API key found with length: {len(api_key)}")
    
    pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates", api_key)
