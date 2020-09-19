import re
from datetime import datetime
from itertools import repeat
from multiprocessing import Pool
from random import shuffle, randint
from time import sleep
from urllib.parse import urlparse

import json
import requests

SPECIAL_CHARACTERS_DICT = dict(
    [
        ("Ã¡", "á"),
        ("Ã ", "à"),
        ("Ã£", "ã"),
        ("Ã¢", "â"),
        ("Ã", "Á"),  # a
        ("Ã©", "é"),
        ("Ãª", "ê"),
        ("Ã³", "ó"),
        ("Ãµ", "õ"),
        ("Ã´", "ô"),
        ("Ãº", "ú"),
        ("Ã", "Ú"),
        ("Ã§", "ç"),
        ("Ã", "í"),
    ]
)

# limit thresholds
#  https://docs.google.com/spreadsheets/d/1f4OZWE1BOtMS7JJcruNh8Rpem-MbmBVnLrERcmP9OZU/edit#gid=0


def multiple_replace(string):
    pattern = re.compile("|".join([re.escape(k) for k in SPECIAL_CHARACTERS_DICT.keys()]), re.M)
    return pattern.sub(lambda x: SPECIAL_CHARACTERS_DICT[x.group(0)], string)


class BaseDataSource(object):
    def __init__(self, name):
        self.name = name

    def get_result(self, query, **kwargs):
        raise NotImplementedError("getResult on " + self.name + " not implemented yet!")

    def to_str(self, list_of_headlines_obj):
        return json.dumps(list(map(lambda obj: obj.encoder(), list_of_headlines_obj)))

    def to_obj(self, list_of_headlines_str):
        return [ResultHeadLine.decoder(x) for x in json.loads(list_of_headlines_str)]


class RoundTripEncoder(json.JSONEncoder):
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
        return super(RoundTripEncoder, self).default(obj)


class ResultHeadLine(object):
    def __init__(self, headline, datetime, domain, url):
        self.headline = headline
        self.datetime = datetime
        self.domain = domain
        self.url = url

    @classmethod
    def decoder(cls, json_str):
        json_obj = json.loads(json_str)
        return cls(
            headline=json_obj["headline"],
            datetime=datetime.strptime(
                json_obj["datetime"],
                "%s %s" % (RoundTripEncoder.DATE_FORMAT, RoundTripEncoder.TIME_FORMAT),
            ),
            domain=json_obj["domain"],
            url=json_obj["url"],
        )

    def encoder(self):
        return json.dumps(self.__dict__, cls=RoundTripEncoder)


class ArquivoPT(BaseDataSource):
    URL_REQUEST = "http://arquivo.pt/textsearch"
    DATETIME_FORMAT = "%Y%m%d%H%M%S"

    def __init__(
        self, max_items_per_site=50, domains_by_request=1, processes=2, docs_per_query=2000
    ):
        BaseDataSource.__init__(self, "ArquivoPT")
        self.max_items_per_site = max_items_per_site
        self.domains_by_request = domains_by_request
        self.processes = processes
        self.docs_per_query = docs_per_query

    def get_result(self, query, **kwargs):
        domains = kwargs["domains"]

        if not domains:
            raise ValueError(
                "Empty domains list. You need to specify at least one domain to restrict the search"
            )

        shuffle(domains)

        interval = (
            kwargs["from"].strftime(ArquivoPT.DATETIME_FORMAT),
            kwargs["to"].strftime(ArquivoPT.DATETIME_FORMAT),
        )

        domains_chunks = [
            domains[i: i + min(self.domains_by_request, len(domains))]
            for i in range(0, len(domains), min(self.domains_by_request, len(domains)))
        ]

        print(domains_chunks)

        # run requests in parallel
        with Pool(processes=self.processes) as pool:
            results_by_domain = pool.starmap(
                self.getResultsByDomain, zip(domains_chunks, repeat(query), repeat(interval))
            )

        all_results = []
        for dominio_list in [
            dominio_list for dominio_list in results_by_domain if dominio_list is not None
        ]:
            all_results.extend(dominio_list)

        return all_results

    def get_all_results(self, domains, params):

        from urllib.parse import unquote

        try:
            response = requests.get(ArquivoPT.URL_REQUEST, params=params, timeout=45)
        except Exception:
            print("Timeout domains =", domains)
            return

        print("RESPONSE CODE: ", response.status_code)
        if response.status_code != 200:
            print("error")

        json_obj = response.json()
        print("estimated_nr_results: ", json_obj['estimated_nr_results'])
        print("nr items: ", len(json_obj['response_items']))
        print("nr. pages: ", int(json_obj['estimated_nr_results']) / self.docs_per_query)
        print()

        has_next = False
        if 'next_page' in json_obj:
            has_next = True
        else:
            print("NO next_page")

        while has_next:
            next_url = unquote(json_obj.get('next_page'))
            print(next_url)
            try:
                response = requests.get(url=next_url, timeout=45)
            except Exception as e:
                print(e)

            if response.status_code != 200:
                print("error")

            json_obj = response.json()
            print(len(json_obj['response_items']))
            print()
            if 'next_page' in json_obj:
                has_next = True

    def getResultsByDomain(self, domains, query, interval):

        itemsPerSite = min(self.max_items_per_site, int(2000 / len(domains)))
        siteSearch = ",".join([urlparse(d).netloc for d in domains])

        # siteSearch = 'publico.pt/politica'

        params = {
            "q": query,
            "from": interval[0],
            "to": interval[1],
            "siteSearch": siteSearch,
            "maxItems": self.docs_per_query,
            "itemsPerSite": itemsPerSite,
            "type": "html",
            "fields": "originalURL,title,tstamp,encoding,linkToArchive",
        }

        print(ArquivoPT.URL_REQUEST)
        print(params)
        print()

        try:
            response = requests.get(ArquivoPT.URL_REQUEST, params=params, timeout=45)

        except Exception:
            print("Timeout domains =", domains)
            return

        if response.status_code != 200:
            return

        json_obj = response.json()

        print("nr items: ", len(json_obj['response_items']))

        results = {}
        for item in json_obj["response_items"]:
            if not (interval[0] < item["tstamp"] < interval[1]):
                continue

            url_domain = urlparse(item["originalURL"]).netloc

            if "Ã" in item["title"]:
                item["title"] = multiple_replace(item["title"])

            try:
                item_result = ResultHeadLine(
                    headline=item["title"],
                    datetime=datetime.strptime(item["tstamp"], ArquivoPT.DATETIME_FORMAT),
                    domain=url_domain,
                    url=item["linkToArchive"],
                )

            except Exception as e:
                print()
                print(e)
                print()
                pass

            if url_domain not in results:
                results[url_domain] = {}

            if (
                item_result.url not in results[url_domain]
                or results[url_domain][item_result.url].datetime > item_result.datetime
            ):
                results[url_domain][item_result.url] = item_result
        result_array = []
        for domain in results.values():
            result_array.extend(list(domain.values()))

        return result_array


def load_politicians():
    names = dict()
    with open('../wikidata/politicians_no_parties.json', 'rt') as f_in:
        data = json.load(f_in)
        for person in data['results']['bindings']:
            person_uri = person['person']['value']
            person_name = person['personLabel']['value']
            names[person_uri] = person_name

    return names


def load_domains():
    domains = []
    with open('data/domains.txt', 'rt') as f_in:
        for line in f_in:
            domains.append(line.strip('\n'))
    return domains


def main():

    domains = load_domains()
    names = load_politicians()

    for idx, (k, v) in enumerate(names.items()):
        print(idx, v)
        sleep_sec = randint(10, 20)
        print("sleeping for", sleep_sec, "secs")
        sleep(sleep_sec)
        wikidata_id = k.split("/")[-1]
        results = query_arquivo(v, domains)
        f_name = '_'.join(v.split()) + '_' + wikidata_id + '.tsv'

        import csv
        with open(f_name, 'wt') as f_out:
            tsv_writer = csv.writer(f_out, delimiter='\t')
            for x in sorted(results, key=lambda i: i.datetime, reverse=False):
                tsv_writer.writerow([str(x.datetime), x.headline, x.url])


def query_arquivo(name, domains):

    params = {
        "domains": domains,
        "from": datetime(year=1996, month=1, day=1),
        "to": datetime(year=2019, month=12, day=31),
    }

    query = '+'.join(name.split())
    apt = ArquivoPT()
    search_result = apt.get_result(query=query, **params)

    headlines = set()
    unique_results = []

    for x in search_result:
        if x.headline in headlines:
            continue
        headlines.add(x.headline)
        unique_results.append(x)

    print("all results:", len(search_result))
    print("unique: ", len(unique_results))

    return unique_results


if __name__ == "__main__":
    main()
