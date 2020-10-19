import os
from typing import Optional, List

import joblib
import pt_core_news_sm
from elasticsearch import Elasticsearch

from fastapi import FastAPI, Query

from politiquices.extraction.utils import clean_title

app = FastAPI()

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, "../classifiers/news_titles/trained_models/")
RESOURCES = os.path.join(APP_ROOT, "resources/")

print("Loading spaCy model...")
nlp_core = pt_core_news_sm.load(disable=["tagger", "parser"])

# ToDo: fail on error
print("Setting up connection with Elasticsearch")
es = Elasticsearch([{"host": "localhost", "port": 9200}])

print("Loading trained models...")
relationship_clf = joblib.load(MODELS + "relationship_clf_2020-10-17_001401.pkl")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/ner")
async def named_entities(news_title: Optional[str] = None):
    title = clean_title(news_title).strip()
    doc = nlp_core(title)
    entities = {ent.text: ent.label_ for ent in doc.ents}
    persons_to_tag = [
        "Marcelo",
        "Passos",
        "Rio",
        "Centeno",
        "Negrão",
        "Relvas",
        "Costa",
        "Coelho",
        "Santana",
        "Alegre",
        "Sócrates",
    ]

    persons = []

    for k, v in entities.items():
        if k in persons_to_tag and v != "PER":
            persons.append(k)
        if v == "PER":
            persons.append(k)

    return persons


@app.get("/relationship")
async def classify_relationship(news_title: str, person: List[str] = Query(None)):
    persons = person
    title = clean_title(news_title).strip()

    if len(persons) < 2:
        return {"not enough entities": person}

    if len(persons) > 2:
        return {"more than 2 entities": person}

    title = title.replace(persons[0], "PER").replace(persons[1], "PER")
    predicted_probs = relationship_clf.tag([title])

    rel_type_scores = {
        label: float(pred)
        for label, pred in zip(relationship_clf.label_encoder.classes_, predicted_probs[0])
    }

    return rel_type_scores


@app.get("/wikidata")
async def wikidata_linking(entity: str):

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
    res = es.search(index="politicians", body={"query": {"query_string": {"query": entity_query}}})

    if res["hits"]["hits"]:
        return {"wiki_id": res["hits"]["hits"][0]["_source"]}

    return {"wiki_id": None}
