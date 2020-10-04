import os
from os import path

import jsonlines as jsonlines
import mmh3
import requests

from politiquices.extraction.utils import clean_title

url_relationship_clf = "http://127.0.0.1:8000/relationship"
url_relevancy_clf = "http://127.0.0.1:8000/relevant"
arquivo_data = "../../data/crawled"


def crawled_data():
    for filename in os.listdir(arquivo_data):
        with jsonlines.open(arquivo_data + "/" + filename, mode="r") as reader:
            for line in reader:
                yield line


def read_hashes():
    if path.exists("../arquivo_pt/processed_titles.jsonl"):
        print("Loading already processed titles...")
        with jsonlines.open('../arquivo_pt/processed_titles.jsonl') as reader:
            return set([obj['hash'] for obj in reader.iter(type=dict, skip_invalid=False)])
    return set()


def process_titles(titles_hashes):
    with jsonlines.open('../arquivo_pt/processed_titles.jsonl', mode='a') as writer:
        for entry in crawled_data():

            cleaned_title = clean_title(entry['title']).strip()

            # ToDo: skip 'desporto'/'desportos' in URL

            # too short skipped
            # maybe increase this a bit? 4 ?
            if len(cleaned_title.split()) <= 2:
                continue

            # already seen skip
            title_hash = mmh3.hash(cleaned_title, signed=False)
            if title_hash in titles_hashes:
                continue

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

            writer.write(processed_entry)

            if relevancy_resp_json['relevant'] > relevancy_resp_json['non-relevant']:
                print(processed_entry)
                print()


def main():
    titles_hashes = read_hashes()
    process_titles(titles_hashes)


if __name__ == "__main__":
    main()
