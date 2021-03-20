import argparse
import json
import concurrent
from datetime import datetime
from datetime import timedelta
from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor

import requests
from loguru import logger

from politiquices.nlp.data_sources.arquivo_pt.utils import load_domains
from politiquices.nlp.utils.utils import just_sleep

# make sure to follow arquivo.pt guidelines for API usage
# https://docs.google.com/spreadsheets/d/1f4OZWE1BOtMS7JJcruNh8Rpem-MbmBVnLrERcmP9OZU/edit#gid=0

OUTPUT_DIR = "crawled"
URL_REQUEST = "http://arquivo.pt/textsearch"

domains_crawled_dates = None


def runner(domains, query, start_date, end_date):
    all_results = defaultdict(list)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {
            executor.submit(query_arquivo, query, url, start_date, end_date):
                url for url in domains
        }
        try:
            for future in concurrent.futures.as_completed(future_to_url, timeout=120):
                url = future_to_url[future]
                data = future.result()
                all_results[url] = data
                logger.info(f'{url}\t{len(data)}')

        except Exception as exc:
            logger.debug(f'{query} generated an exception: {exc}')

    return all_results


def query_arquivo(query, domain, start_date, end_date, timeout=10, n_attempts=10):

    # ToDo: do more queries to the same domain for smaller time intervals
    params = {
        "q": query,
        "from": start_date,
        "to": end_date,
        "siteSearch": domain,
        "maxItems": 2000,
        "dedupField": 'title',
        "type": "html",
        "fields": "title, tstamp, linkToArchive",
    }

    for i in range(n_attempts):
        if i > 0:
            print(query, domain, "attempt: ", i)
        try:
            just_sleep(3)
            response = requests.get(URL_REQUEST, params=params, timeout=timeout+(i*3))
            if response.status_code == 200:
                response_dict = response.json()
                return response_dict['response_items']
            logger.info(f'{domain}\t{response.reason}\t{response.status_code}')
        except Exception as exc:
            print("Exception: ", exc)
            print(query, domain)

    return None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entity", help="entity query")
    parser.add_argument("--start_date", help="from date")
    parser.add_argument("--end_date", help="to date")
    args = parser.parse_args()
    return args


def main():

    args = parse_args()
    start_date = args.start_date
    end_date = args.end_date
    query_name = args.entity

    # domains to be crawled
    domains = load_domains()

    # domains crawled span times
    with open('config_data/domains_crawled_dates.json') as f_in:
        global domains_crawled_dates
        domains_crawled_dates = json.load(f_in)

    today = datetime.today()
    today_minus_1_year = today - timedelta(days=365)
    today_minus_1_year_str = today_minus_1_year.strftime("%Y%m%d")

    print(f"querying: {query_name} {start_date} {today_minus_1_year_str}")
    results = runner(domains, query_name, start_date, today_minus_1_year_str)

    for r, v in results.items():
        print(r)
        for x in v:
            print(x['tstamp'], x['title'])
            print()
        print("\n\n---")


if __name__ == '__main__':
    main()
