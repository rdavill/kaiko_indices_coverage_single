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
        debug_print(f"Processing base ticker: {base
