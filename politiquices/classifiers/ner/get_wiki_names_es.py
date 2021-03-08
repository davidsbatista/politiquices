from elasticsearch import Elasticsearch


def main():
    es = Elasticsearch([{"host": "localhost", "port": 9200}])
    res = es.search(index="politicians", body={"query": {"match_all": {}}, "size": 2000})
    names_and_aliases = sorted([(r["_source"]["label"], r['_source']['aliases'])
                                for r in res["hits"]["hits"]], key=lambda x: len(x[0]),
                               reverse=True)

    with open('names_token_patterns.txt', 'wt') as f_out:
        for wiki_name, alias in names_and_aliases:
            f_out.write(wiki_name+'\n')


if __name__ == "__main__":
    main()
