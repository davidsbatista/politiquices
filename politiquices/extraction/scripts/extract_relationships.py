import os
import sys
from functools import lru_cache

import joblib
import requests
from elasticsearch import Elasticsearch
from jsonlines import jsonlines

from politiquices.extraction.classifiers.ner.rule_based_ner import RuleBasedNer
from politiquices.extraction.utils import clean_title

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, "../classifiers/news_titles/trained_models/")
RESOURCES = os.path.join(APP_ROOT, "resources/")

print("Loading relationship classifier...")
relationship_clf = joblib.load(MODELS + "relationship_clf_2020-10-17_001401.pkl")

print("Setting up connection with Elasticsearch")
es = Elasticsearch([{"host": "localhost", "port": 9200}])


@lru_cache(maxsize=500000)
def entity_linking_api(entity):
    payload = {'entity': entity}
    response = requests.request("GET", "http://127.0.0.1:8000/wikidata", params=payload)
    return response.json()


@lru_cache(maxsize=500000)
def entity_linking(entity):

    def needs_escaping(char):
        escape_chars = {
            "\\": True,
            "+": True,
            "-": True,
            "!": True,
            "(": True,
            ")": True,
            ":": True,
            "^": True,
            "[": True,
            "]": True,
            '"': True,
            "{": True,
            "}": True,
            "~": True,
            "*": True,
            "?": True,
            "|": True,
            "&": True,
            "/": True,
        }
        return escape_chars.get(char, False)

    # ToDo: add more from PER_entities.txt
    mappings = {
        "Carrilho": "Manuela Maria Carrilho",
        "Costa": "António Costa",
        "Durão": "Durão Barroso",
        "Ferreira de o Amaral": "Joaquim Ferreira do Amaral",
        "Jerónimo": "Jerónimo de Sousa",
        "Marcelo": "Marcelo Rebelo de Sousa",
        "Marques Mendes": "Luís Marques Mendes",
        "Menezes": "Luís Filipe Menezes",
        "Moura Guedes": "Manuela Moura Guedes",
        "Nobre": "Fernando Nobre",
        "Portas": "Paulo Portas",
        "Rebelo de Sousa": "Marcelo Rebelo de Sousa",
        "Relvas": "Miguel Relvas",
        "Santana": "Pedro Santana Lopes",
        "Santos Silva": "Augusto Santos Silva",
        "Soares": "Mário Soares",
        "Sousa Tavares": "Miguel Sousa Tavares",
    }

    sanitized = ""
    for character in entity:
        if needs_escaping(character):
            sanitized += "\\%s" % character
        else:
            sanitized += character

    entity_clean = mappings.get(sanitized, sanitized)
    entity_query = " AND ".join([token.strip() for token in entity_clean.split()])
    print(entity, "\t", sanitized, "\t", entity_query)
    res = es.search(index="politicians",
                    body={"query": {"query_string": {"query": entity_query}}})

    if res["hits"]["hits"]:
        return {"wiki_id": res["hits"]["hits"][0]["_source"]}

    return {"wiki_id": None}


def main():

    rule_ner = RuleBasedNer()

    processed = jsonlines.open('titles_processed.jsonl', mode='w')
    more_entities = jsonlines.open('titles_processed_more_entities.jsonl', mode='w')
    no_entities = jsonlines.open('titles_processed_no_entities.jsonl', mode='w')
    no_relation = jsonlines.open('titles_processed_no_relation.jsonl', mode='w')
    no_wiki = jsonlines.open('titles_processed_no_wiki_id.jsonl', mode='w')

    count = 0
    with jsonlines.open(sys.argv[1]) as f_in:
        for line in f_in:

            count += 1
            if count % 1000 == 0:
                print(count)

            cleaned_title = clean_title(line['title']).strip()
            # persons = get_persons(cleaned_title)
            persons = rule_ner.tag(cleaned_title)

            if len(persons) == 2:
                title_PER = cleaned_title.replace(persons[0], "PER").replace(persons[1], "PER")
                predicted_probs = relationship_clf.tag([title_PER])
                rel_type_scores = {
                    label: float(pred)
                    for label, pred in
                    zip(relationship_clf.label_encoder.classes_, predicted_probs[0])
                }

                if rel_type_scores['other'] > 0.5:
                    no_relation.write({'title': cleaned_title,
                                       'entities': persons,
                                       'scores': rel_type_scores,
                                       'linkToArchive': line['linkToArchive'],
                                       'tstamp': line['tstamp']
                                       })
                    continue

                entity = entity_linking(persons[0])
                ent_1 = entity['wiki_id'] if entity['wiki_id'] else None
                entity = entity_linking(persons[1])
                ent_2 = entity['wiki_id'] if entity['wiki_id'] else None

                print(entity_linking.cache_info())

                result = {
                    'title': cleaned_title,
                    'entities': persons,
                    'ent_1': ent_1,
                    'ent_2': ent_2,
                    'scores': rel_type_scores,
                    'linkToArchive': line['linkToArchive'],
                    'tstamp': line['tstamp']
                }

                if ent_1 is None or ent_2 is None:
                    no_wiki.write(result)
                else:
                    processed.write(result)

            elif len(persons) > 2:
                more_entities.write({'title': cleaned_title, 'entities': persons})

            else:
                no_entities.write({'title': cleaned_title, 'entities': persons})

    no_entities.close()
    more_entities.close()
    no_wiki.close()
    no_relation.close()
    processed.close()


if __name__ == '__main__':
    main()
