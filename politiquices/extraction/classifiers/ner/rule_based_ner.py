import os
import re

from elasticsearch import Elasticsearch
from spacy.pipeline import EntityRuler

connectors = ['do', 'da', 'de', 'dos']
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
entities_file = os.path.join(APP_ROOT, "PER_entities.txt")


def get_names_kb():
    es = Elasticsearch([{"host": "localhost", "port": 9200}])
    res = es.search(index="politicians",
                    body={"query": {"match_all": {}},
                          "size": 2000})
    all_names = sorted([r['_source']['label'] for r in res['hits']['hits']])

    return all_names


def build_entity_patterns(kb_names):
    names = set()

    for name in kb_names:
        name_clean = re.sub(r'\(.*\)', '', name)    # remove text inside parenthesis
        name_clean = re.sub(r'(,.*)', ' ',  name_clean)  # remove comma and all text after
        name_parts = name_clean.split()
        names.add(name_clean)

        # first and last name
        if len(name_parts) > 2:
            first_and_last = name_parts[0]+' '+name_parts[-1]
            names.add(first_and_last)

        # skip second name
        if len(name_parts) > 3:
            end = ' '.join(name_parts[len(name_parts) - 2:])
            skip_second = name_parts[0]+' '+end
            names.add(skip_second)

        # last 3 names
        if len(name_parts) > 3:
            last_three = name_parts[-3:]
            if any(x == last_three[0] for x in connectors):
                last_three = last_three[1:]

            names.add(' '.join(last_three))

    return list(names)


def get_names_file(fname):
    with open(fname, 'rt') as f_in:
        names = {line.strip() for line in f_in if not line.startswith('#')}
    return list(names)


def build_ner(names):
    import pt_core_news_sm
    nlp = pt_core_news_sm.load(disable=["tagger", "parser"])

    patterns = []
    for x in sorted(names, key=lambda x: len(x), reverse=True):
        patterns.append({'label': 'PER', 'pattern': x})

    ruler_single_token = EntityRuler(nlp, overwrite_ents=True)
    ruler_single_token.add_patterns(patterns)
    ruler_single_token.name = 'single_token'

    ruler_two_tokens = EntityRuler(nlp)
    ruler_two_tokens.add_patterns([
        {'label': 'PER', 'pattern': 'Marinho e Pinto'},
        {'label': 'PER', 'pattern': 'Ribeiro e Castro'}
     ])
    ruler_two_tokens.name = 'two_tokens'

    nlp.add_pipe(ruler_two_tokens, before="ner")
    nlp.add_pipe(ruler_single_token, after="ner")

    return nlp


def get_rule_based_ner():
    all_names = get_names_kb()
    patterns_one = build_entity_patterns(all_names)
    patterns_two = get_names_file(entities_file)
    nlp = build_ner(patterns_one + patterns_two)
    return nlp


def main():
    # see: https://spacy.io/usage/rule-based-matching

    nlp = get_rule_based_ner()

    samples = [
        "Marinho e Pinto saiu do armário",
        "Ribeiro e Castro 'silenciado' pelo CDS",
        "Passos Coelho diz que ministro da Educação cede a interesses dos sindicatos",
        "Costa irrita-se com Pedro Santos",
        "António Costa irrita-se com Jerónimo de Sousa",
        "AR - Rio gostou do debate. ″As pessoas não têm que estar a guerrear-se com violência″",
        "PSD e CDS querem ouvir Marcelo, Freitas e Castro Caldas",
    ]

    for s in samples:
        doc = nlp(s)
        persons = [ent.text for ent in doc.ents if ent.label_ == 'PER']
        print(s, '\t', persons, len(persons))


if __name__ == '__main__':
    main()
