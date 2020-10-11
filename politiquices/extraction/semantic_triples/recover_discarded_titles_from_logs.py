import os
import sys
from collections import defaultdict
from os import path

import jsonlines
import mmh3
import requests

from politiquices.extraction.utils import clean_title

url_relationship_clf = "http://127.0.0.1:8000/relationship"
url_relevancy_clf = "http://127.0.0.1:8000/relevant"
arquivo_data = "../../data/crawled"

entities = defaultdict(str)
freq = defaultdict(int)


def get_wiki(entity):
    url = 'http://127.0.0.1:8000/wikidata'
    payload = {'entity': entity}
    r = requests.get(url, params=payload)

    if r.json()['wiki_id'] is not None and entity not in entities:
        entities[entity] = r.json()['wiki_id']

    return r.json()


def main():
    titles_hashes = set()

    with jsonlines.open(sys.argv[1]) as reader:
        for line in reader:

            # ToDo: ignore title with 'Benfica|Sporting|Porto|Desporto'
            if 'desporto' in line['entry']['linkToArchive']:
                continue

            entry = line['entry']
            cleaned_title = clean_title(entry['title']).strip()

            if cleaned_title == 'Keynes / Hayek':
                continue

            # too short skip
            if len(cleaned_title.split()) < 4:
                continue

            if line['relevancy']['relevant'] < 0.5:
                continue

            # already seen skip
            title_hash = mmh3.hash(cleaned_title, signed=False)
            if title_hash in titles_hashes:
                continue

            titles_hashes.add(title_hash)

            # print(cleaned_title)
            # print(line['relationship'])
            # scores = [(k, v) for k, v in line['relationship'].items() if isinstance(v, float)]
            # rel = sorted(scores, key=lambda x: x[1], reverse=True)[0]
            # print(rel[0], rel[1])

            # print(line['relationship']['entity_1'], end='\t')
            if line['relationship']['entity_1_wiki']:
                # print(line['relationship']['entity_1_wiki']['wiki'])
                pass
            else:
                wiki = get_wiki(line['relationship']['entity_1'])
                # print(wiki)

            # print(line['relationship']['entity_2'], end='\t')
            if line['relationship']['entity_2_wiki']:
                # print(line['relationship']['entity_2_wiki']['wiki'])
                pass
            else:
                wiki = get_wiki(line['relationship']['entity_2'])
                # print(wiki)

            # print("\n\n")

            freq[line['relationship']['entity_1']] += 1
            freq[line['relationship']['entity_2']] += 1

            """
            payload = {"news_title": cleaned_title}
            relevancy_resp = requests.request("GET", url_relevancy_clf, params=payload)
            relevancy_resp_json = relevancy_resp.json()
            relationship_resp_json = None
            if relevancy_resp_json['relevant'] > relevancy_resp_json['non-relevant']:
                relationship_resp = requests.request("GET", url_relationship_clf, params=payload)
                relationship_resp_json = relationship_resp.json()

            processed_entry = {
                "hash": title_hash,
                "entry": entry,
                "cleaned_title": cleaned_title,
                "relevancy": relevancy_resp_json,
                "relationship": relationship_resp_json}

            # print(processed_entry)
            # writer.write(processed_entry)

            if relevancy_resp_json['relevant'] > relevancy_resp_json['non-relevant']:
                print(processed_entry)
                print("\n------------------------")
            """

    sorted_dict = {k: v for k, v in sorted(freq.items(), key=lambda item: item[1], reverse=True)}
    for k, v in sorted_dict.items():
        print(k, '\t', v, '\t', end='')
        wiki = get_wiki(k)
        print(wiki)

    """
    print("-----------------------\n")
    for k in sorted(freq, key=lambda x: freq[x], reverse=True):
        print(k, v)
    """


if __name__ == "__main__":
    main()
