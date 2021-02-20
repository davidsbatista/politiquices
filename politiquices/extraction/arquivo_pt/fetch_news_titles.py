import concurrent
import json
from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor

import requests
from jsonlines import jsonlines
from loguru import logger

from politiquices.extraction.utils.utils import load_domains, just_sleep

# https://docs.google.com/spreadsheets/d/1f4OZWE1BOtMS7JJcruNh8Rpem-MbmBVnLrERcmP9OZU/edit#gid=0

OUTPUT_DIR = "crawled"
URL_REQUEST = "http://arquivo.pt/textsearch"

domains_crawled_dates = None


def load_entities():
    names = []
    with open('data/entities_names.txt', 'rt') as f_in:
        for line in f_in:
            if not line.startswith('#') and len(line) > 1:
                names.append(line.strip('\n'))
    return names


def runner(domains, query):
    all_results = defaultdict(list)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(query_arquivo, query, url): url for url in domains}
        try:
            for future in concurrent.futures.as_completed(future_to_url, timeout=120):
                url = future_to_url[future]
                data = future.result()
                all_results[url] = data
                # start_date = domains_crawled_dates[url]['first_crawl']
                # end_date = domains_crawled_dates[url]['last_crawl']
                logger.info(f'{url}\t{len(data)}')
                # ToDo: log success for query,url,from,to

        except Exception as exc:
            logger.debug(f'{query} generated an exception: {exc}')

    return all_results


def query_arquivo(query, domain, timeout=10, n_attempts=10):

    # ToDo: do more queries to the same domain for smaller time intervals
    params = {
        "q": query,
        "from": domains_crawled_dates[domain]['first_crawl'],
        "to": domains_crawled_dates[domain]['last_crawl'],
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


def main():
    domains = load_domains()
    names = load_entities()

    print("querying:")
    print(f'{len(domains)} domains')
    print(f'{len(names)} entities')
    print()

    # read domains crawled span times
    with open('data/domains_crawled_dates.json') as f_in:
        global domains_crawled_dates
        domains_crawled_dates = json.load(f_in)

    for name in names:
        print(name)
        f_name = '_'.join(name.split()) + '.jsonl'
        results = runner(domains, name)
        if results:
            with jsonlines.open(OUTPUT_DIR+"/"+f_name, mode='w') as writer:
                for k, v in results.items():
                    for r in v:
                        writer.write(r)


if __name__ == '__main__':
    main()
