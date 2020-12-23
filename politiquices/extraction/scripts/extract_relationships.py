import os
import sys
import pickle
from functools import lru_cache

from elasticsearch import Elasticsearch
from jsonlines import jsonlines
from keras.models import load_model

from politiquices.extraction.classifiers.ner.rule_based_ner import RuleBasedNer
from politiquices.extraction.classifiers.news_titles.models.lstm_with_atten import Attention
from politiquices.extraction.classifiers.news_titles.relationship_direction_clf import \
    detect_direction
from politiquices.extraction.utils.utils import clean_title_re, clean_title_quotes

import pt_core_news_lg

print("Loading spaCy NLP model")
nlp = pt_core_news_lg.load()
nlp.disable = ["tagger", "parser", "ner"]

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, "../classifiers/news_titles/trained_models/")
RESOURCES = os.path.join(APP_ROOT, "resources/")

print("Setting up connection with Elasticsearch")
es = Elasticsearch([{"host": "localhost", "port": 9200}])


def read_att_normal_models():

    """
    print("Loading relevancy classifier...")
    with open(MODELS + "relevancy_clf_2020-12-05_160642.pkl", "rb") as f_in:
        relevancy_clf = pickle.load(f_in)
    model = load_model(
        MODELS + "relevancy_clf_2020-12-05_160642.h5", custom_objects={"Attention": Attention}
    )
    relevancy_clf.model = model
    """

    print("Loading relationship classifier...")
    with open(MODELS + "relationship_clf_2020-12-05_164644.pkl", "rb") as f_in:
        relationship_clf = pickle.load(f_in)
    model = load_model(
        MODELS + "relationship_clf_2020-12-05_164644.h5", custom_objects={"Attention": Attention}
    )
    relationship_clf.model = model

    return relationship_clf, None


@lru_cache(maxsize=500000)
def entity_linking(entity, all_results=False):

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
        "Carrilho": "Manuel Maria Carrilho",
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
    # print(entity, "\t", sanitized, "\t", entity_query)
    res = es.search(index="politicians", body={"query": {"query_string": {"query": entity_query}}})

    if res["hits"]["hits"]:
        if all_results:
            return res["hits"]["hits"]
        return {"wiki_id": res["hits"]["hits"][0]["_source"]}

    if all_results:
        return []

    return {"wiki_id": None}


def main():

    # set up the NER system
    rule_ner = RuleBasedNer()

    # load named-entities that should be ignored
    with open('ner_ignore.txt', 'rt') as f_in:
        ner_ignore = [line.strip() for line in f_in.readlines()]

    # relationship_clf, relevancy_clf = read_avg_weighted_att_models()
    relationship_clf, relevancy_clf = read_att_normal_models()

    # open files for logging and later diagnostic
    no_entities = jsonlines.open("titles_processed_no_entities.jsonl", mode="w")
    more_entities = jsonlines.open("titles_processed_more_entities.jsonl", mode="w")
    no_wiki = jsonlines.open("titles_processed_no_wiki_id.jsonl", mode="w")
    processed = jsonlines.open("titles_processed.jsonl", mode="w")
    ner_linked = jsonlines.open("ner_linked.jsonl", mode="w")
    ner_ignored = jsonlines.open("ner_ignored.jsonl", mode="w")

    count = 0
    with jsonlines.open(sys.argv[1]) as f_in:
        for line in f_in:

            count += 1

            if count % 1000 == 0:
                print(count)

            cleaned_title = clean_title_quotes(clean_title_re(line["title"]))
            persons = rule_ner.tag(cleaned_title)
            if any(person in persons for person in ner_ignore):
                ner_ignored.write({"title": cleaned_title, "entities": persons})
                continue

            if len(persons) == 2:

                # NER
                title_PER = cleaned_title.replace(persons[0], "PER").replace(persons[1], "PER")

                # ToDo: before entity linking try to expand the named-entity
                # https://arquivo.pt/textextracted?m=<original_url>/<crawl_date>

                # entity linking
                entity = entity_linking(persons[0])
                ent_1 = entity["wiki_id"] if entity["wiki_id"] else None
                entity = entity_linking(persons[1])
                ent_2 = entity["wiki_id"] if entity["wiki_id"] else None
                print(entity_linking.cache_info())

                # relationship classification
                predicted_probs = relationship_clf.tag([title_PER])
                rel_type_scores = {
                    label: float(pred)
                    for label, pred in zip(
                        relationship_clf.label_encoder.classes_, predicted_probs[0]
                    )
                }

                # detect relationship direction
                doc = nlp(cleaned_title)
                pos_tags = [(t.text, t.pos_, t.tag_) for t in doc]
                pred, pattern = detect_direction(pos_tags, persons[0], persons[1])

                new_scores = dict()
                for k, v in rel_type_scores.items():
                    predicted = pred.replace('rel', k)
                    new_scores[predicted] = v

                result = {
                    "title": cleaned_title,
                    "entities": persons,
                    "ent_1": ent_1,
                    "ent_2": ent_2,
                    "scores": new_scores,
                    "linkToArchive": line["linkToArchive"],
                    "tstamp": line["tstamp"],
                }

                if ent_1 is None or ent_2 is None:
                    no_wiki.write(result)
                else:
                    processed.write(result)

                ner_linked.write({"ner": persons[0], "wiki": result['ent_1']})
                ner_linked.write({"ner": persons[1], "wiki": result['ent_2']})

            elif len(persons) > 2:
                more_entities.write({"title": cleaned_title, "entities": persons})

            else:
                no_entities.write({"title": cleaned_title, "entities": persons})

    no_entities.close()
    more_entities.close()
    no_wiki.close()
    processed.close()


if __name__ == "__main__":
    main()
