import requests
import json
import csv
import os
import sys
from datetime import datetime, timedelta

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
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index', 'KT5', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'March 19, 2018', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index NYC', 'KT5NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'March 19, 2018', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index LDN', 'KT5LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'March 19, 2018', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index SGP', 'KT5SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'March 19, 2018', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index', 'KT10', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'March 18, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index NYC', 'KT10NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'March 18, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index LDN', 'KT10LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'March 18, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index SGP', 'KT10SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'March 18, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index', 'KT15', 'N/A', 'N/A', 'Real-time (5 sec)', 'October 17, 2023', 'December 23, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index NYC', 'KT15NYC', 'N/A', 'N/A', 'NYC Fixing', 'October 17, 2023', 'December 23, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index LDN', 'KT15LDN', 'N/A', 'N/A', 'LDN Fixing', 'October 17, 2023', 'December 23, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index SGP', 'KT15SGP', 'N/A', 'N/A', 'SGP Fixing', 'October 17, 2023', 'December 23, 2019', '-', '-', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Vinter 21Shares Crypto Basket Equal Weight Index ', 'HODLV', 'N/A', 'N/A', 'LDN Fixing', 'September 29, 2021', 'January 01, 2021', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/multi-asset_hodlv_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Blue-Chip', 'Vinter 21Shares Crypto Basket 10 Index', 'HODLX', 'N/A', 'N/A', 'LDN Fixing', 'September 29, 2021', 'January 01, 2021', '-', '-', '<a target="_blank">Coming Soon</a>'),
        ('Kaiko', 'Blue-Chip', 'Vinter Valour Digital Asset Basket 10 Index', 'VDAB10', 'N/A', 'N/A', 'LDN Fixing', 'July 21, 2022', 'January 01, 2021', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/VDAB10%20-%20Fact%20Sheet%20-%20multi-asset_vdab10_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Blue-Chip', 'Vinter Pando Crypto Basket 6 Index ', 'PANDO6', 'N/A', 'N/A', '17:00 CET Fixing', 'July 21, 2022', 'January 01, 2021', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/PANDO6%20-%20Fact%20Sheet%20-%20multi-asset_pando6_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Blue-Chip', 'Virtune Vinter Crypto Top 10 Index', 'VVT10', 'N/A', 'N/A', '17:00 CET Fixing', 'March 31, 2023', 'January 01, 2021', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/VVT10%20-%20Fact%20Sheet%20-%20multi-asset_vvt10_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),

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
        ('Kaiko', 'Sector & Thematic', 'Vinter Cardano Yield Index ', 'CASL', 'N/A', 'N/A', 'LDN Fixing', 'November 10, 2022', 'March 06, 2024', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/CASL%20-%20Fact%20Sheet%20-%20multi-asset_casl_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Sector & Thematic', 'Sygnum Platform Winners Index ', 'MOON', 'N/A', 'N/A', '17:00 CET Fixing', 'July 21, 2022', 'November 01, 2019', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/MOON%20-%20Fact%20Sheet%20-%20multi-asset_moon_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Sector & Thematic', 'Vinter CF Crypto Web3 Index', 'VCFWB3', 'N/A', 'N/A', 'LDN Fixing', 'May 15, 2023', 'January 01, 2021', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/VCFWB3%20-%20Fact%20Sheet%20-multi-asset_vcfwb3_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),

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
        ('Kaiko', 'Market', 'Kaiko Investable Index SGP', 'KMINVSGP', 'N/A', 'N/A', 'SGP Fixing', 'January 23, 2025', 'April 1, 2014', '-', '-', factsheet_market),
        ('Kaiko', 'Market', 'Vinter 21Shares Crypto Mid-Cap Index ', 'ALTS', 'N/A', 'N/A', 'LDN Fixing', 'December 14, 2021', 'January 01, 2021', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/ALTS%20-%20Fact%20Sheet%20-%20multi-asset_alts_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter 21Shares Crypto Staking Index ', 'STAKE', 'N/A', 'N/A', 'LDN Fixing', 'January 18, 2023', 'January 01, 2021', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/multi-asset_stake_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter BOLD Index', 'VBNGD', 'N/A', 'N/A', 'LDN Fixing', 'November 10, 2023', 'January 01, 2020', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/VBNGD%20-%20Fact%20Sheet%20-%20multi-asset_vbngd_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter CF Crypto Momentum Index', 'VCFMOM', 'N/A', 'N/A', 'LDN Fixing', 'May 15, 2023', 'January 01, 2021', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/VCFMOM%20-%20Fact%20Sheet%20-multi-asset_vcfmom_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter Diffuse Digital 30 Index', 'DDV', 'N/A', 'N/A', 'LDN Fixing', 'July 02, 2022', 'January 01, 2021', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/DDV%20-%20Fact%20Sheet%20-%20multi-asset_ddv_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter Hashdex Risk Parity Momentum Crypto Index', 'VHASHMOM', 'N/A', 'N/A', '17:00 CET Fixing', 'September 05, 2022', 'January 01, 2021', '-', '-', '<a href="https://marketing.kaiko.com/hubfs/VHASHMOM%20Kaiko%20Factsheet.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter Bytetree BOLD1 Inverse Volatility Index', 'BOLD1', 'N/A', 'N/A', 'LDN Fixing', 'November 10, 2023', 'January 01, 2020', '-', '-', '<a target="_blank">Coming Soon</a>')
    ]

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
            debug_print(f"Response content: {response.text[:200]}...")  # Log partial response
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
        return '-', '-'
    
    # Only process certain types
    if asset_type not in ['Reference_Rate', 'Benchmark_Reference_Rate', 'Single-Asset', 'Custom_Rate']:
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
        
        # Check the publication time and filter if before 9pm UTC yesterday
        if 'time' in data:
            try:
                # Parse the time field
                publication_time = datetime.strptime(data['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
                debug_print(f"Publication time for {ticker}: {publication_time.isoformat()}Z")
                
                if publication_time < yesterday_9pm_utc:
                    debug_print(f"🚫 Excluding {ticker} - publication time {publication_time.isoformat()}Z is before cutoff {yesterday_9pm_utc.isoformat()}Z")
                    return 'EXCLUDE', 'EXCLUDE'  # Special return value to indicate exclusion
                    
            except ValueError as e:
                debug_print(f"⚠️ Could not parse time field for {ticker}: {data.get('time', 'N/A')} - {e}")
        else:
            debug_print(f"⚠️ No 'time' field found in response for {ticker}")
        
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
    """Fetch reference rates and save them to CSV, excluding entries with Coinbase in exchanges."""
    debug_print("Starting data pull and save process")
    existing_fact_sheets = get_existing_fact_sheets()
    fixed_items = get_fixed_entries()
    
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

    headers = [
        'Brand', 'Benchmark Family', 'Name', 'Ticker', 'Base', 'Quote',
        'Dissemination', 'Launch Date', 'Inception Date', 'Exchanges', 'Calculation Window', 'Factsheet'
    ]

    # Use the URL as-is
    debug_print(f"Fetching API data from: {api_url}")
    
    # Don't need API key for reference data
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
        
        # Count of reference rate types after filtering
        reference_rate_count = 0
        
        for item in usd_items:
            ticker = item['ticker']
            asset_type = item['type']
            
            # Count reference rate types
            if asset_type in ['Reference_Rate', 'Benchmark_Reference_Rate']:
                reference_rate_count += 1
            
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
            
            # Fetch exchanges & calculation window using the exchange mappings
            exchanges, calc_window = fetch_historical_prices_data(ticker, asset_type, api_key, exchange_mappings)
            
            api_items.append((
                brand, normalized_family, short_name, ticker, base_short_name, quote_short_name,
                dissemination, launch_date, inception, exchanges, calc_window, fact_sheet
            ))
        
        debug_print(f"Found {reference_rate_count} reference rate items after USD filtering")
        
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
        
        # Filter out items with Coinbase in exchanges before saving
        filtered_items = []
        coinbase_count = 0
        for item in all_items:
            exchanges_column = item[9]  # Exchanges is the 10th column (index 9)
            if "Coinbase" not in exchanges_column:
                filtered_items.append(item)
            else:
                coinbase_count += 1
                debug_print(f"Excluding {item[3]} due to Coinbase in exchanges: {exchanges_column}")
        
        debug_print(f"Filtered from {len(all_items)} to {len(filtered_items)} items (removed {coinbase_count} Coinbase entries)")
        
        # Check for items with non-default exchanges and calculation windows
        non_default_count = sum(1 for item in filtered_items if item[9] != '-' or item[10] != '-')
        debug_print(f"Items with non-default exchanges or calculation windows: {non_default_count}")
        
        # Save to CSV with filtered items
        main_csv_path = "Reference_Rates_Coverage.csv"
        debug_print(f"Saving main CSV to {os.path.abspath(main_csv_path)}")
        with open(main_csv_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)
            writer.writerows(filtered_items)
        
        # Write the filtered CSV with only entries that have factsheets (also excluding Coinbase)
        write_filtered_csv(filtered_items, headers)
        debug_print("Process complete")
        
    else:
        debug_print(f"❌ Error fetching API data: {response.status_code}")

# Main execution
if __name__ == "__main__":
    debug_print("Starting script execution...")

    # Retrieve API key from environment
    api_key = os.environ.get('KAIKO_API_KEY') or os.environ.get('API_KEY')
    
    # Log environment variables for debugging (safely)
    debug_print("Environment variables related to API key:")
    for key in os.environ:
        if 'KEY' in key or 'API' in key:
            debug_print(f"Found environment variable: {key} (value hidden)")
    
    if not api_key:
        debug_print("⚠️ Warning: API key is missing! Exchanges and Calculation Window columns will show '-'.")
        api_key = ""  # Use empty string instead of None to avoid errors
    else:
        # Log partial key for debugging
        debug_print(f"API key found with length: {len(api_key)}")
    
    # Remove the quote=usd parameter since we're now filtering in the code
    pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates", api_key)
