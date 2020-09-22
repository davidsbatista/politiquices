import os
import json
import sys

from elasticsearch import Elasticsearch
from elasticsearch import helpers


def create_index():
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    # es.indices.delete(index='politica_titles')

    request_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1
        },
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


def main():
    bulk_data = []
    path = sys.argv[1]
    for file in os.listdir(path):
        if not file.endswith("json"):
            continue
        with open(path+"/"+file, 'rt') as f_in:
            data = json.load(f_in)
            wiki_id = file.split(".json")[0]
            data_keys = data['entities'][wiki_id]
        if 'pt' in data_keys['labels']:
            label = data_keys['labels']['pt']['value']
        else:
            label = None
            print("no pt found in labels")
        if 'pt' in data_keys['aliases']:
            aliases = [aliases['value'] for aliases in data_keys['aliases']['pt']]
        else:
            aliases = None

        print("wiki: ", wiki_id)
        print("last_modified", data_keys['modified'])
        print("label: ", label)
        print("aliases: ", aliases)
        print("--------------------")

        """
        # ToDo: extende aliases for some cases
        if label == 'António Costa':
            aliases.append("Costa")
        """

        doc = {
            'wiki': wiki_id,
            'last_modified': data_keys['modified'],
            'label': label,
            'aliases': aliases,
        }

        bulk_data.append(json.dumps(doc))

    es = create_index()

    print("Bulk indexing")
    print(len(bulk_data))
    res = helpers.bulk(es, bulk_data, index='politicians')
    print(res)

    # check data is in there, and structure in there
    es.search(body={"query": {"match_all": {}}}, index='politicians')


if __name__ == '__main__':
    main()