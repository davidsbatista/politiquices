import os
import sys
import json

from elasticsearch import Elasticsearch
from elasticsearch import helpers

from rdflib import Graph


def create_index():
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
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


def parse_file(f_name):
    wiki_id = f_name.split("/")[-1][:-4]
    g = Graph()
    with open(f_name, 'rt') as f_in:
        g.parse(f_in, format="turtle")

    # get name
    query = f"""SELECT DISTINCT ?name
                WHERE {{ 
                    wd:{wiki_id} rdfs:label ?name . FILTER(LANG(?name) = "pt")
                }}"""
    names = [str(row.asdict()['name']) for row in g.query(query)]

    # get alternative names
    query = f"""SELECT DISTINCT ?alternative
                WHERE {{ 
                    OPTIONAL {{
                        wd:{wiki_id} skos:altLabel ?alternative . FILTER(LANG(?alternative) = "pt")
                    }}
                }}"""
    alternative_names = [str(row.asdict()['alternative']) for row in g.query(query)]

    print()
    print(names)
    print(alternative_names)
    print("\n\n----------------------")
    exit(-1)


def main():
    bulk_data = []
    path = sys.argv[1]
    for file in os.listdir(path):
        if not file.endswith("ttl"):
            continue
        parse_file(path + "/" + file)

        """
        # P106 : occupation
        # P39  : position held
        # P69  : educated_at
        # P102 : partido politico
        # P18  : image link
        doc = {
            'wiki': wiki_id,
            'last_modified': data_keys['modified'],
            'label': label,
            'aliases': aliases,
        }
        bulk_data.append(json.dumps(doc))
        """

    """
    es = create_index()
    print("Bulk indexing")
    print(len(bulk_data))
    res = helpers.bulk(es, bulk_data, index='politicians')
    print(res)

    # check data is in there, and structure in there
    es.search(body={"query": {"match_all": {}}}, index='politicians')
    """


if __name__ == '__main__':
    main()
