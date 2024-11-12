import requests
import json
import csv
from datetime import datetime


def pull_and_save_data_to_csv(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        data = json.loads(response.text)

        items = []
        for item in data['data']:
            ticker = item['ticker']
            brand = item['brand']
            quote_short_name = item['quote']['short_name'].upper()
            base_short_name = item['base']['short_name'].upper()
            type = item['type'].replace('_', ' ')
            dissemination = item['dissemination']
            short_name = item['short_name'].replace('_', ' ')
            launch_date = datetime.strptime(item['launch_date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')
            inception = datetime.strptime(item['inception_date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')

            items.append((ticker, brand, quote_short_name, base_short_name, type, dissemination, short_name, launch_date, inception))

        headers = ['Ticker','Brand', 'Quote (short name)', 'Base (short name)', 'Type', 'Dissemination', 'Rate Short name', 'Launch Date', 'Inception']
        sorted_items = sorted(items, key=lambda row: row[2])

        with open("Reference_Rates_Coverage.csv", "w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(sorted_items)

pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates")
