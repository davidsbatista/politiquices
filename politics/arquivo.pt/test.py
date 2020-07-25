from datetime import datetime
from urllib.parse import unquote

import requests

URL_REQUEST = "http://arquivo.pt/textsearch"
DATETIME_FORMAT = "%Y%m%d%H%M%S"


def main():
    query = "Obama"
    params = {
        "q": query,
        "from": datetime(year=1996, month=1, day=1).strftime(DATETIME_FORMAT),
        "to": datetime(year=2019, month=12, day=31).strftime(DATETIME_FORMAT),
        "siteSearch": 'publico.pt',
        "maxItems": 500,
        "itemsPerSite": 1,
        "type": "html",
        "fields": "title, tstamp, originalURL, linkToArchive",
    }

    response = requests.get(URL_REQUEST, params=params, timeout=45)
    response_dict = response.json()

    for item in response_dict['response_items']:
        for k, v in item.items():
            print(k, '\t', v)
        print()

    unquote(response_dict['next_page'])


if __name__ == '__main__':
    main()
