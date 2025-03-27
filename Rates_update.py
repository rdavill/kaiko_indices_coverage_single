def get_exchange_name_mappings():
    """
    Fetch exchange codes and names from the reference API and create a mapping.
    Returns a dictionary with exchange codes as keys and exchange names as values.
    """
    debug_print("Fetching exchange name mappings from reference API")
    url = "https://reference-data-api.kaiko.io/v1/exchanges"
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            debug_print(f"❌ Failed to fetch exchange mappings: {response.status_code}")
            return {}
            
        data = response.json()
        debug_print(f"Exchange API response received with {len(data)} items")
        
        # Sample some data for debugging
        if len(data) > 0:
            debug_print(f"Sample exchange data: {data[0:2]}")
        
        # Create mapping of code -> name
        mappings = {}
        for exchange in data:
            if 'code' in exchange and 'name' in exchange:
                code = exchange['code']
                name = exchange['name']
                
                # Special case for CRCO
                if code == 'CRCO':
                    mappings[code] = 'Crypto.com'
                else:
                    mappings[code] = name
        
        debug_print(f"✅ Successfully fetched {len(mappings)} exchange mappings")
        
        # Print some sample mappings for debugging
        sample_keys = list(mappings.keys())[:5] if len(mappings) > 5 else list(mappings.keys())
        for key in sample_keys:
            debug_print(f"Sample mapping: {key} -> {mappings[key]}")
            
        return mappings
        
    except Exception as e:
        debug_print(f"❌ Error fetching exchange mappings: {str(e)}")
        return {}

def fetch_historical_prices_data(ticker, asset_type, api_key, exchange_mappings=None):
    """
    Fetch historical price data for Reference_Rate, Benchmark_Reference_Rate, and Single-Asset.
    Uses exchange_mappings to convert exchange codes to full names.
    """
    debug_print(f"Fetching historical prices data for ticker: {ticker}, Type: {asset_type}")

    # Load exchange mappings if not provided
    if exchange_mappings is None:
        debug_print("No exchange mappings provided, fetching new ones")
        exchange_mappings = get_exchange_name_mappings()
        debug_print(f"Loaded {len(exchange_mappings)} exchange mappings on demand")
    else:
        debug_print(f"Using provided exchange mappings with {len(exchange_mappings)} items")

    # If no API key provided, return default values
    if not api_key:
        debug_print(f"No API key provided, skipping historical data fetch for {ticker}")
        return '-', '-'
    
    # Only process certain types
    if asset_type not in ['Reference_Rate', 'Benchmark_Reference_Rate', 'Single-Asset']:
        debug_print(f"Skipping ticker {ticker} (type: {asset_type}) - Not a reference rate.")
        return '-', '-'
    
    # Build URL with page_size=1, sort=desc and parameters=true - this gets the most recent data point efficiently
    url = f"https://us.market-api.kaiko.io/v2/data/index.v1/digital_asset_rates_price/{ticker}?page_size=1&parameters=true&sort=desc"
    
    headers = {'X-API-KEY': api_key, 'Accept': 'application/json'}
    
    try:
        debug_print(f"Making API request to: {url}")
        response = requests.get(url, headers=headers, timeout=15)

        debug_print(f"Response Status Code: {response.status_code}")

        if response.status_code != 200:
            debug_print(f"❌ API call failed with status {response.status_code}: {response.text}")
            return '-', '-'
            
        data = response.json()
        
        # Check if we have data
        if not data.get('data') or len(data['data']) == 0:
            debug_print(f"⚠️ No data found for ticker: {ticker}")
            return '-', '-'
        
        # Get the first interval (should be the most recent one due to sort=desc)
        first_interval = data['data'][0]
        
        # Extract exchanges and calc_window directly from parameters
        exchanges = '-'
        calc_window = '-'
        
        if 'parameters' in first_interval:
            params = first_interval['parameters']
            
            # Get exchanges
            if 'exchanges' in params and params['exchanges']:
                exchanges_list = params['exchanges']
                debug_print(f"Found exchange codes for {ticker}: {exchanges_list}")
                
                # Map exchange codes to full names using our mappings
                mapped_exchanges = []
                for exchange_code in sorted(exchanges_list):
                    # Map exchange code to full name, with special case for CRCO
                    if exchange_code in exchange_mappings:
                        mapped_name = exchange_mappings[exchange_code]
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
            
            # Get calculation window
            if 'calc_window' in params:
                calc_window = f"{params['calc_window']}s"
                debug_print(f"Found calculation window for {ticker}: {calc_window}")
            else:
                debug_print(f"No calculation window found in parameters for {ticker}")
        else:
            debug_print(f"No parameters found in response for {ticker}")
        
        debug_print(f"✅ Success: {ticker} - Exchanges: {exchanges}, Calculation Window: {calc_window}")
        return exchanges, calc_window

    except requests.exceptions.RequestException as e:
        debug_print(f"🚨 RequestException: {e}")
        return '-', '-'
    except Exception as e:
        debug_print(f"🚨 Unexpected error processing {ticker}: {str(e)}")
        return '-', '-'
