import csv
import os
import requests
from pprint import pprint

url_relationship_clf = "http://127.0.0.1:8000/relationship"
url_relevancy_clf = "http://127.0.0.1:8000/relevant"

arquivo_data = "../../data/crawled"


def crawled_data():
    for filename in os.listdir(arquivo_data):
        with open(arquivo_data+"/"+filename, newline="") as csvfile:
            arquivo = csv.reader(csvfile, delimiter="\t", quotechar="|")
            for row in arquivo:
                yield {"date": row[0], "title": row[1], "url": row[2]}


def main():

    for sentence in crawled_data():
        payload = {"news_title": sentence['title']}
        response = requests.request("GET", url_relevancy_clf, params=payload)
        resp_json = response.json()
        if resp_json['relevant'] > resp_json['non-relevant']:
            print(sentence['title'])
            print(response.json())
            response = requests.request("GET", url_relationship_clf, params=payload)
            pprint(response.json())
            print()


if __name__ == "__main__":
    main()
