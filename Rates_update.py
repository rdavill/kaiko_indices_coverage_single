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
    
    # Remove location suffixes - need to check for _NYC, _LDN, _SGP
    if cleaned_ticker.endswith('_NYC'):
        return cleaned_ticker[:-4]  # Remove '_NYC'
    elif cleaned_ticker.endswith('_LDN'):
        return cleaned_ticker[:-4]  # Remove '_LDN'  
    elif cleaned_ticker.endswith('_SGP'):
        return cleaned_ticker[:-4]  # Remove '_SGP'
    
    return cleaned_ticker

def clean_name(name):
    """Remove location suffixes from name."""
    # Remove location suffixes from the end of names
    for suffix in [' NYC', ' LDN', ' SGP']:
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name

def get_dissemination_type_from_ticker(ticker):
    """
    Determine dissemination type based on ticker suffix:
    - No suffix (base ticker) = Real-time
    - _NYC suffix = Daily Fixing NYC
    - _LDN suffix = Daily Fixing LDN  
    - _SGP suffix = Daily Fixing SGP
    """
    cleaned_ticker = ticker.rstrip('_')
    
    if cleaned_ticker.endswith('_NYC'):
        return 'daily_fixing', 'NYC'
    elif cleaned_ticker.endswith('_LDN'):
        return 'daily_fixing', 'LDN'
    elif cleaned_ticker.endswith('_SGP'):
        return 'daily_fixing', 'SGP'
    else:
        # Base ticker (no location suffix) = Real-time
        return 'realtime', None

def check_learn_more_url(ticker):
    """
    Checks if the 'Learn more' URL for a given ticker returns a 200 status code.
    Returns True if the URL is valid (200 OK), False otherwise.
    """
    url = f"https://explorer.kaiko.com/rates/{ticker}"
    try:
        debug_print(f"Checking URL status for {url}")
        response = requests.head(url, timeout=10) 
        if response.status_code == 200:
            debug_print(f"✅ URL {url} is valid (200 OK)")
            return True
        else:
            debug_print(f"❌ URL {url} returned status code {response.status_code}")
            return False
    except Exception as e:
        debug_print(f"🚨 Error checking URL {url}: {e}")
        return False

def merge_location_variants(items):
    """
    Merge location-based variants into single rows with combined disseminations.
    Uses ticker suffix to determine dissemination type:
    - Base ticker (no suffix) = Real-time
    - _NYC/_LDN/_SGP suffix = Daily Fixing for that location
    """
    debug_print("Starting merge of location variants for single assets")
    
    # Group items by base ticker
    ticker_groups = OrderedDict()
    
    for item in items:
        original_ticker = item[2]  # Original ticker is at index 2
        base_ticker = get_base_ticker(original_ticker)
        
        debug_print(f"GROUPING: {original_ticker} -> base: {base_ticker}")
        
        if base_ticker not in ticker_groups:
            ticker_groups[base_ticker] = []
        
        ticker_groups[base_ticker].append(item)
    
    debug_print(f"\nGROUPING SUMMARY:")
    for base_ticker, variants in ticker_groups.items():
        debug_print(f"  Base: {base_ticker} has {len(variants)} variants:")
        for variant in variants:
            debug_print(f"    - {variant[2]}")
    
    merged_items = []
    
    # Process each group
    for base_ticker, variants in ticker_groups.items():
        debug_print(f"\n=== PROCESSING: {base_ticker} with {len(variants)} variants ===")
        
        # If only one variant, check if it should be merged anyway
        if len(variants) == 1:
            debug_print(f"  Only one variant for {base_ticker}: {variants[0][2]}")
        
        # Use first variant as template for name
        base_variant = variants[0]
        cleaned_name = clean_name(base_variant[1])
        clean_base_ticker = base_ticker.rstrip('_')
        
        # Collect dissemination info from ALL variants based on ticker suffix
        daily_fixing_locations = set()
        has_realtime = False
        
        for variant in variants:
            original_ticker = variant[2]
            dissem_type, location = get_dissemination_type_from_ticker(original_ticker)
            
            debug_print(f"  Analyzing {original_ticker}: {dissem_type} {location or '(none)'}")
            
            if dissem_type == 'realtime':
                has_realtime = True
                debug_print(f"    -> Real-time found")
            elif dissem_type == 'daily_fixing' and location:
                daily_fixing_locations.add(location)
                debug_print(f"    -> Daily fixing {location} found")
        
        # Build dissemination string
        dissemination_parts = []
        
        if daily_fixing_locations:
            # Sort locations in preferred order
            location_order = ['SGP', 'LDN', 'NYC']
            sorted_locations = [loc for loc in location_order if loc in daily_fixing_locations]
            dissemination_parts.append(f"Daily Fixing {', '.join(sorted_locations)}")
        
        if has_realtime:
            dissemination_parts.append("Real-time (5s)")
        
        combined_disseminations = ', '.join(dissemination_parts)
        
        debug_print(f"    FINAL DISSEMINATION: {combined_disseminations}")
        
        # Check the 'Learn more' URL
        if not check_learn_more_url(clean_base_ticker):
            debug_print(f"🚫 Excluding {clean_base_ticker} - Learn more URL check failed")
            continue
        
        # Create the 'Learn more' link
        learn_more_link = f'<a href="https://explorer.kaiko.com/rates/{clean_base_ticker}" target="_blank">Explore performance</a>'
        
        # Create merged entry
        merged_entry = (
            "Benchmark Reference Rate",  # Family
            cleaned_name,               # Name
            clean_base_ticker,          # Base Ticker
            combined_disseminations,    # Dissemination(s)
            learn_more_link            # Learn more
        )
        
        merged_items.append(merged_entry)
        debug_print(f"✅ CREATED ENTRY: {clean_base_ticker} -> {combined_disseminations}")
    
    debug_print(f"\nFINAL RESULT: {len(merged_items)} merged entries from {len(items)} original items")
    return merged_items

def pull_and_save_data_to_csv(api_url, api_key):
    """Fetch single-asset reference rates and save them to CSV with screenshot columns only."""
    debug_print("Starting data pull and save process (processing all records)")
    
    headers = [
        'Family', 'Name', 'Base Ticker', 'Dissemination(s)', 'Learn more'
    ]
    
    response = requests.get(api_url)
    if response.status_code == 200:
        data = json.loads(response.text)
        api_items = []
        
        # Filter for USD quote items only
        usd_items = [item for item in data['data'] if item['quote']['short_name'].upper() == 'USD']
        debug_print(f"Filtered to {len(usd_items)} USD quote items")
        
        for item in usd_items:
            ticker = item['ticker']
            asset_type = item['type']
            
            # Only process Reference_Rate and Benchmark_Reference_Rate
            if asset_type not in ['Reference_Rate', 'Benchmark_Reference_Rate']:
                continue
            
            short_name = item['short_name'].replace('_', ' ')
            dissemination = item['dissemination']  # We'll ignore this and use ticker suffix instead
            
            debug_print(f"COLLECTING: {ticker} (API says: {dissemination})")
            
            api_items.append((
                asset_type,
                short_name,
                ticker,
                dissemination  # This will be ignored in favor of ticker-based logic
            ))
        
        debug_print(f"COLLECTED {len(api_items)} items for processing")
        
        # Merge location variants
        merged_items = merge_location_variants(api_items)
        
        # Save to CSV
        main_csv_path = "Reference_Rates_Coverage.csv"
        with open(main_csv_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)
            writer.writerows(merged_items)
        
        print(f"\nSaved {len(merged_items)} merged records to {main_csv_path}")
        
        # Print first few rows for verification
        print("\nFirst 5 rows:")
        for i, row in enumerate(merged_items[:5]):
            print(f"{i+1}: {row[1]} ({row[2]}) -> {row[3]}")
        
    else:
        debug_print(f"❌ Error fetching API data: {response.status_code}")

# Main execution
if __name__ == "__main__":
    api_key = os.environ.get("KAIKO_API_KEY", "")
    pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates", api_key)
