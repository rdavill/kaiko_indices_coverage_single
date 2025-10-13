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

def check_learn_more_url(ticker):
    """
    Checks if the 'Learn more' URL for a given ticker returns a 200 status code.
    Returns True if the URL is valid (200 OK), False otherwise.
    """
    url = f"https://explorer.kaiko.com/rates/{ticker}"
    try:
        debug_print(f"Checking URL status for {url}")
        # Use HEAD request for efficiency as we only need the status code
        response = requests.head(url, timeout=10) 
        if response.status_code == 200:
            debug_print(f"✅ URL {url} is valid (200 OK)")
            return True
        else:
            debug_print(f"❌ URL {url} returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        debug_print(f"🚨 Connection error checking URL {url}")
        return False
    except requests.exceptions.Timeout:
        debug_print(f"🚨 Timeout (10s) checking URL {url}")
        return False
    except requests.exceptions.RequestException as e:
        debug_print(f"🚨 Request error checking URL {url}: {e}")
        return False
    except Exception as e:
        debug_print(f"🚨 Unexpected error checking URL {url}: {e}")
        return False

def merge_location_variants(items):
    """
    Merge location-based variants into single rows with combined disseminations,
    preserving original order, and filtering out rows with invalid 'Learn more' URLs.
    Group real-time rates with daily fixings.
    """
    debug_print("Starting merge of location variants for single assets")
    
    # Use OrderedDict to preserve insertion order
    ticker_groups = OrderedDict()
    ticker_order = []  # Track the order in which base tickers first appear
    
    for item in items:
        original_ticker = item[2]  # Original ticker is at index 2
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
            original_ticker = variant[2]
            cleaned_ticker = original_ticker.rstrip('_')
            if get_base_ticker(original_ticker) == base_ticker and not any(cleaned_ticker.endswith(suffix) for suffix in ['NYC', 'LDN', 'SGP']):
                base_variant = variant
            else:
                location_variants.append(variant)
        
        if base_variant is None:
            # If no base variant found, use the first one as base
            base_variant = variants[0]
            location_variants = variants[1:]
        
        # Build disseminations string - group real-time with daily fixings
        disseminations = []
        
        # Check base variant dissemination
        base_dissemination = base_variant[3]  # Dissemination is at index 3
        if base_dissemination == "Real-time (5s)":
            disseminations.append("Daily Fixing SGP, NYC, LDN")
        else:
            disseminations.append(base_dissemination)
        
        # Add location disseminations in order: NYC, LDN, SGP
        locations_found = []
        for location in ['NYC', 'LDN', 'SGP']:
            for variant in location_variants:
                original_ticker = variant[2]
                cleaned_ticker = original_ticker.rstrip('_')
                if cleaned_ticker.endswith(location):
                    variant_dissem = variant[3]
                    if variant_dissem == "Real-time (5s)":
                        # Real-time variants are already grouped above
                        pass
                    else:
                        locations_found.append(location)
                    break
        
        if locations_found:
            disseminations.extend(locations_found)
        
        combined_disseminations = ', '.join(disseminations)
        
        # Clean the name by removing location suffixes
        cleaned_name = clean_name(base_variant[1])
        
        # Ensure base_ticker has no trailing underscores
        clean_base_ticker = base_ticker.rstrip('_')
        
        # Check the 'Learn more' URL for 404
        if not check_learn_more_url(clean_base_ticker):
            debug_print(f"🚫 Excluding {clean_base_ticker} - Learn more URL check failed (404 or error).")
            continue # Skip this item if the URL is not valid

        # Create the 'Learn more' link using the clean_base_ticker
        learn_more_link = f'<a href="https://explorer.kaiko.com/rates/{clean_base_ticker}" target="_blank">Explore performance</a>'

        # Create merged entry with only the columns from the screenshot
        merged_entry = (
            "Benchmark Reference Rate",  # Family (hardcoded based on screenshot)
            cleaned_name,               # Name
            clean_base_ticker,          # Base Ticker
            combined_disseminations,    # Dissemination(s)
            learn_more_link            # Learn more
        )
        
        merged_items.append(merged_entry)
        debug_print(f"Merged {clean_base_ticker}: {cleaned_name} -> {combined_disseminations}")
    
    debug_print(f"Merged {len(items)} initial items into {len(merged_items)} final entries after URL validation")
    return merged_items

def pull_and_save_data_to_csv(api_url, api_key):
    """Fetch single-asset reference rates and save them to CSV with screenshot columns only."""
    debug_print("Starting data pull and save process for single-asset rates")
    
    # Headers matching the screenshot
    headers = [
        'Family', 'Name', 'Base Ticker', 'Dissemination(s)', 'Learn more'
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
            
            short_name = item['short_name'].replace('_', ' ')
            dissemination = item['dissemination']
            
            # Store only the data we need for the final columns
            api_items.append((
                asset_type,      # Will be mapped to Family
                short_name,      # Name
                ticker,          # Base Ticker (will be cleaned)
                dissemination    # Dissemination(s)
            ))
        
        debug_print(f"Found {single_asset_count} single-asset items after USD filtering")
        debug_print(f"Processing {len(api_items)} items")
        
        # Merge location variants and apply URL filtering
        merged_items = merge_location_variants(api_items)
        
        # Save to CSV with merged items
        main_csv_path = "Reference_Rates_Coverage.csv"
        debug_print(f"Saving main CSV to {os.path.abspath(main_csv_path)}")
        with open(main_csv_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)
            writer.writerows(merged_items)
        
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
