import csv
import os
from os import path

import jsonlines as jsonlines
import mmh3
import requests

from politics.utils import clean_sentence

url_relationship_clf = "http://127.0.0.1:8000/relationship"
url_relevancy_clf = "http://127.0.0.1:8000/relevant"
arquivo_data = "../../data/crawled"


# ToDo:
"""
def filter_sentences_persons(titles):
    # filter only the ones with at least two 'PER'
    # ToDo: add also 'PER' from a hand-crafted list,
    #  see: https://spacy.io/usage/rule-based-matching
    wrong_PER = load_wrong_per()
    print(f"Extracting named-entities from {len(titles)} titles")
    titles_doc = [(t[0], nlp(t[1]), t[2]) for t in titles]
    titles_per = []
    for title in titles_doc:
        persons = [ent.text for ent in title[1].ents if ent.label_ == "PER"]
        if len(persons) == 2:
            if not set(persons).intersection(set(wrong_PER)):
                titles_per.append((title, persons))

    return titles_per
"""


def crawled_data():
    for filename in os.listdir(arquivo_data):
        with open(arquivo_data + "/" + filename, newline="") as csvfile:
            arquivo = csv.reader(csvfile, delimiter="\t", quotechar="|")
            for row in arquivo:
                yield {"date": row[0], "title": row[1], "url": row[2]}


def read_hashes():
    if path.exists("processed_titles.jsonl"):
        print("Loading already processed titles...")
        with jsonlines.open('processed_titles.jsonl') as reader:
            return set([obj['hash'] for obj in reader.iter(type=dict, skip_invalid=False)])
    return set()


def main():
    titles_hashes = read_hashes()
    with jsonlines.open('processed_titles.jsonl', mode='a') as writer:
        for entry in crawled_data():
            cleaned_title = clean_sentence(entry['title']).strip()

            # too short skipped
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


if __name__ == "__main__":
    main()
