import os
import sys
import json

from elasticsearch import Elasticsearch
from elasticsearch import helpers

from rdflib import Graph


def create_index():
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    # ToDo: if index exists delete
    # es.indices.delete(index='politicians')

    request_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1
        },

        # ToDo:
        'mappings': {
            'properties': {
                'date': {'type': 'text'},
                'url': {'type': 'keyword'},
                'title': {'type': 'text'},
            }}
    }
    print("creating 'politicians' index...")
    es.indices.create(index='politicians', body=request_body)

    return es


def get_name_alternative_names(f_name, wiki_id):
    g = Graph()
    with open(f_name, 'rt') as f_in:
        g.parse(f_in, format="turtle")

    # name
    query_name = f"""SELECT DISTINCT ?name
                WHERE {{ 
                    wd:{wiki_id} wdt:P31 wd:Q5 .
                    wd:{wiki_id} rdfs:label ?name . FILTER(LANG(?name) = "pt") 
                }}"""

    # alternative names
    query_alt_names = f"""SELECT DISTINCT ?alternative
                      WHERE {{
                          wd:{wiki_id} wdt:P31 wd:Q5 . 
                          OPTIONAL {{ 
                                wd:{wiki_id} skos:altLabel ?alternative . 
                                FILTER(LANG(?alternative) = "pt") 
                          }} 
                      }}"""
    name = [str(row.asdict()['name']) for row in g.query(query_name)]
    alternative_names = [str(row.asdict()['alternative']) for row in g.query(query_alt_names)]

    return name, alternative_names


def main():
    bulk_data = []
    path = sys.argv[1]
    counter = 0
    for file in os.listdir(path):
        if not file.endswith("ttl"):
            continue
        wiki_id = file.split("/")[-1][:-4]
        name, alternative = get_name_alternative_names(path + "/" + file, wiki_id)
        if name:
            doc = {
                'wiki_id': wiki_id,
                'label': name[0],
                'aliases': alternative}
            bulk_data.append(doc)
        counter += 1
        print(f"{counter}/{len(os.listdir(path))}")

    # save the processed results into file, useful if the next step fails, don't need
    # to repeat the whole process again
    with open('wiki_names_alternative_names.jsonl', 'wt') as f_out:
        for d in bulk_data:
            f_out.write(json.dumps(d, ensure_ascii=False)+'\n')

    es = create_index()
    print("Bulk indexing")
    print(len(bulk_data))
    res = helpers.bulk(es, bulk_data, index='politicians')
    print(res)

    # quick check
    es.search(body={"query": {"match_all": {}}}, index='politicians')


if __name__ == '__main__':
    main()
    # ToDo: add args to selective download a specific list of entities
