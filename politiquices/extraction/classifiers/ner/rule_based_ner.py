import re

from elasticsearch import Elasticsearch
from spacy.pipeline import EntityRuler

connectors = ['do', 'da', 'de', 'dos']


def get_names_kb():
    es = Elasticsearch([{"host": "localhost", "port": 9200}])
    res = es.search(index="politicians",
                    body={"query": {"match_all": {}},
                          "size": 2000})
    all_names = sorted([r['_source']['label'] for r in res['hits']['hits']])

    return all_names


def build_entity_patterns(names):
    patterns = []

    for name in names:
        name_clean = re.sub(r'\(.*\)', '', name)
        name_parts = name_clean.split()
        patterns.append({"label": "PER", "pattern": name_clean})

        # first and last
        if len(name_parts) > 2:
            first_and_last = name_parts[0]+' '+name_parts[-1]
            patterns.append({"label": "PER", "pattern": first_and_last})

        # skip second name
        if len(name_parts) > 3:
            end = ' '.join(name_parts[len(name_parts) - 2:])
            skip_second = name_parts[0]+' '+end
            patterns.append({"label": "PER", "pattern": skip_second})

        # last 3
        if len(name_parts) > 3:
            last_three = name_parts[-3:]

            if any(x == last_three[0] for x in connectors):
                last_three = last_three[1:]

            patterns.append({"label": "PER", "pattern": last_three})

    return patterns


def get_names_file(fname):
    with open(fname, 'rt') as f_in:
        pass


def main():
    all_names = get_names_kb()
    patterns = build_entity_patterns(all_names)
    print(len(patterns))

    import pt_core_news_sm
    nlp = pt_core_news_sm.load(disable=["tagger", "parser"])
    ruler = EntityRuler(nlp)
    ruler.add_patterns(patterns)
    nlp.add_pipe(ruler, before="ner")
    # see: https://spacy.io/usage/rule-based-matching


if __name__ == '__main__':
    main()
