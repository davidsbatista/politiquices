import json
import requests


URL_REQUEST = "http://arquivo.pt/wayback/cdx"


def load_domains():
    domains = []
    with open("config_data/domains.txt", "rt") as f_in:
        for line in f_in:
            if not line.startswith("#") and len(line) > 1:
                domains.append(line.strip("\n"))
    return domains


def get_domain_crawl_timeline(domain):
    params = {
        "url": domain,
        "output": "json",
    }

    try:
        response = requests.get(URL_REQUEST, params=params, timeout=20)
        resp = [json.loads(x) for x in response.text.split("\n") if x]
        return {"first_crawl": resp[0]["timestamp"], "last_crawl": resp[-1]["timestamp"]}
    except Exception as exc:
        print('%r generated an exception: %s' % (domain, exc))


def main():
    domains = load_domains()
    crawled_timelines = dict()
    for d in domains:
        print(d)
        crawled_timelines[d] = get_domain_crawl_timeline(d)

    with open('config_data/domains_crawled_dates.json', 'wt') as f_out:
        json.dump(crawled_timelines, f_out, indent=4)


if __name__ == "__main__":
    main()
