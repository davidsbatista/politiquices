import concurrent
from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import unquote

from jsonlines import jsonlines
from loguru import logger

import requests

from politics.arquivo_pt.utils import load_domains
from politics.utils import just_sleep

# https://docs.google.com/spreadsheets/d/1f4OZWE1BOtMS7JJcruNh8Rpem-MbmBVnLrERcmP9OZU/edit#gid=0

URL_REQUEST = "http://arquivo.pt/textsearch"


def runner(domains, query):
    # ToDo: what can go wrong? how to account for possible errors and save all results
    # ToDo: log all the success and failed queries

    print(f'querying for {len(domains)} domains')

    all_results = defaultdict(list)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:

        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(query_arquivo, query, url): url for url in domains}

        try:
            for future in concurrent.futures.as_completed(future_to_url, timeout=0.00001):
                url = future_to_url[future]
                http_code, data = future.result()
                # ToDo: add query,url,from,to
                # ToDo: log if there was an error, query_arquivo() return HTTP codes and result
                if http_code == 200:
                    print(url, len(data), query)
                    all_results[url] = data
                else:
                    print(http_code)
                # ToDo: log success for query,url,from,to

        except Exception as exc:
            print('%r generated an exception: %s' % (query, exc))

    return all_results


def query_arquivo(query, domain):

    # just_sleep(5)

    params = {
        "q": query,
        "siteSearch": domain,
        "maxItems": 2000,
        "dedupField": 'title',
        "type": "html",
        "fields": "title, tstamp, linkToArchive",
    }
    # print("querying: ", domain)
    response = requests.get(URL_REQUEST, params=params, timeout=20)

    if response.status_code == 200:
        response_dict = response.json()
        return 200, response_dict['response_items']

    return response.status_code, None


def load_entities():
    names = []
    with open('data/entities_names.txt', 'rt') as f_in:
        for line in f_in:
            if not line.startswith('#') and len(line) > 1:
                names.append(line.strip('\n'))
    return names


def main():
    domains = load_domains()
    names = load_entities()

    # ToDo: read domains crawled span times

    for name in names:
        print(name)
        f_name = '_'.join(name.split()) + '.jsonl'
        results = runner(domains[:4], name)
        if results:
            with jsonlines.open(f_name, mode='w') as writer:
                for k, v in results.items():
                    for r in v:
                        writer.write(r)


if __name__ == '__main__':
    main()
