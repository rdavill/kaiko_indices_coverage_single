import requests
import json
import csv
import os
from datetime import datetime


def pull_and_save_data_to_csv(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        data = json.loads(response.text)

        items = []
        for item in data['data']:
            ticker = item['ticker']
            quote_short_name = item['quote']['short_name'].upper()
            base_short_name = item['base']['short_name'].upper()
            type = item['type'].replace('_', ' ')
            dissemination = item['dissemination']
            short_name = item['short_name'].replace('_', ' ')
            inception = datetime.strptime(item['inception_date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')

            items.append((ticker, quote_short_name, base_short_name, type, dissemination, short_name, inception))

        headers = ['Ticker', 'Quote (short name)', 'Base (short name)', 'Type', 'Dissemination', 'Rate Short name', 'Inception']
        rows = items

        sorted_items = sorted(items, key=lambda row: row[2])

        with open("Reference_Rates_Coverage.csv", "w") as csv_file:  # Simplified the path
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(sorted_items)

pull_and_save_data_to_csv("https://us.market-api.kaiko.io/v2/data/index_reference_data.v1/rates")
