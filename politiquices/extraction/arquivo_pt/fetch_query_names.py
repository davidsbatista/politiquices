
from elasticsearch import Elasticsearch
from politiquices.extraction.utils.utils import write_iterator_to_file

es = Elasticsearch([{"host": "localhost", "port": 9200}])


def get_names():
    res = es.search(index="politicians", body={"query": {"match_all": {}}}, size=2000)
    # for now ignore 'aliases' doc['_source']['aliases']
    return sorted([doc['_source']['label'] for doc in res['hits']['hits']])


if __name__ == '__main__':
    names = get_names()
    write_iterator_to_file(names, 'data/entities_names.txt')
