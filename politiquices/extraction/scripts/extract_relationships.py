import os
import sys
import pickle
from functools import lru_cache

import numpy as np
from elasticsearch import Elasticsearch
from jsonlines import jsonlines
from keras.models import load_model

from politiquices.extraction.classifiers.news_titles.lstm_with_atten import KerasTextClassifier
from politiquices.extraction.classifiers.ner.rule_based_ner import RuleBasedNer
from politiquices.extraction.classifiers.news_titles.relationship_clf import Attention
from politiquices.extraction.utils import clean_title_re, clean_title_quotes

from timer import Timer

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, "../classifiers/news_titles/trained_models/")
RESOURCES = os.path.join(APP_ROOT, "resources/")


print("Setting up connection with Elasticsearch")
es = Elasticsearch([{"host": "localhost", "port": 9200}])


def read_normal_models():
    # ToDo
    pass


def read_att_normal_models():
    print("Loading relevancy classifier...")
    with open(MODELS + "relevancy_clf_2020-12-05_160642.pkl", "rb") as f_in:
        relevancy_clf = pickle.load(f_in)
    model = load_model(
        MODELS + "relevancy_clf_2020-12-05_160642.h5", custom_objects={"Attention": Attention}
    )
    relevancy_clf.model = model

    print("Loading relationship classifier...")
    with open(MODELS + "relationship_clf_2020-12-05_164644.pkl", "rb") as f_in:
        relationship_clf = pickle.load(f_in)
    model = load_model(
        MODELS + "relationship_clf_2020-12-05_164644.h5", custom_objects={"Attention": Attention}
    )
    relationship_clf.model = model

    return relationship_clf, relevancy_clf


def read_avg_weighted_att_models():
    print("Loading relevancy classifier...")
    relevancy_clf = KerasTextClassifier()
    relevancy_clf.load(MODELS + "relevancy_clf")

    print("Loading relationship classifier...")
    relationship_clf = KerasTextClassifier()
    relationship_clf.load(MODELS + "relationship_clf")

    return relationship_clf, relevancy_clf


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
    # print(entity, "\t", sanitized, "\t", entity_query)
    res = es.search(index="politicians", body={"query": {"query_string": {"query": entity_query}}})

    if res["hits"]["hits"]:
        return {"wiki_id": res["hits"]["hits"][0]["_source"]}

    return {"wiki_id": None}


def main():

    # set up the NER system
    rule_ner = RuleBasedNer()

    # relationship_clf, relevancy_clf = read_avg_weighted_att_models()
    relationship_clf, relevancy_clf = read_att_normal_models()

    # open files for logging and later diagnostic
    no_relation = jsonlines.open("extraction_spacy_small/titles_processed_no_relation.jsonl", mode="w")
    no_entities = jsonlines.open("extraction_spacy_small/titles_processed_no_entities.jsonl", mode="w")
    more_entities = jsonlines.open("extraction_spacy_small/titles_processed_more_entities.jsonl", mode="w")
    no_wiki = jsonlines.open("extraction_spacy_small/titles_processed_no_wiki_id.jsonl", mode="w")
    processed = jsonlines.open("extraction_spacy_small/titles_processed.jsonl", mode="w")

    count = 0
    with jsonlines.open(sys.argv[1]) as f_in:
        for line in f_in:
            count += 1
            if count % 1000 == 0:
                print(count)

            try:
                cleaned_title = clean_title_quotes(clean_title_re(line["title"]))
            except Exception as e:
                print(e)
                print("failed to clean ---> ", line["title"])

            # read_avg_weighted_att_models
            """
            predicted_probs = relevancy_clf.predict_proba([cleaned_title])[0]
            pred_labels = relevancy_clf.encoder.inverse_transform([np.argmax(predicted_probs)])
            relevancy_scores = {
                label: float(pred)
                for label, pred in zip(relevancy_clf.encoder.classes_, predicted_probs)
            }
            
            if pred_labels != ["relevant"]:
            no_relation.write(
                {
                    "title": cleaned_title,
                    "scores": relevancy_scores,
                    "linkToArchive": line["linkToArchive"],
                    "tstamp": line["tstamp"],
                }
            )
            continue                
            """

            # read_att_normal_models
            predicted_probs = relevancy_clf.tag([cleaned_title])[0]
            relevancy_scores = {
                label: float(pred)
                for label, pred in zip(relevancy_clf.label_encoder.classes_, predicted_probs)
            }

            if relevancy_scores["relevant"] < 0.5:
                no_relation.write(
                    {
                        "title": cleaned_title,
                        "scores": relevancy_scores,
                        "linkToArchive": line["linkToArchive"],
                        "tstamp": line["tstamp"],
                    }
                )
                continue

            persons = rule_ner.tag(cleaned_title)

            if len(persons) == 2:

                title_PER = cleaned_title.replace(persons[0], "PER").replace(persons[1], "PER")

                # read_att_normal_models
                predicted_probs = relationship_clf.tag([title_PER])
                rel_type_scores = {
                    label: float(pred)
                    for label, pred in zip(
                        relationship_clf.label_encoder.classes_, predicted_probs[0]
                    )
                }

                # read_avg_weighted_att_models
                """
                predicted_probs = relationship_clf.predict_proba([title_PER])
                rel_type_scores = {
                    label: float(pred)
                    for label, pred in zip(
                        relationship_clf.encoder.classes_, predicted_probs[0]
                    )
                }
                """

                entity = entity_linking(persons[0])
                ent_1 = entity["wiki_id"] if entity["wiki_id"] else None
                entity = entity_linking(persons[1])
                ent_2 = entity["wiki_id"] if entity["wiki_id"] else None

                print(entity_linking.cache_info())

                result = {
                    "title": cleaned_title,
                    "entities": persons,
                    "ent_1": ent_1,
                    "ent_2": ent_2,
                    "scores": rel_type_scores,
                    "linkToArchive": line["linkToArchive"],
                    "tstamp": line["tstamp"],
                }

                if ent_1 is None or ent_2 is None:
                    no_wiki.write(result)
                else:
                    processed.write(result)

            elif len(persons) > 2:
                more_entities.write({"title": cleaned_title, "entities": persons})

            else:
                no_entities.write({"title": cleaned_title, "entities": persons})

    no_entities.close()
    more_entities.close()
    no_wiki.close()
    no_relation.close()
    processed.close()


if __name__ == "__main__":
    main()
