import re
import os
from typing import Optional

import joblib
import pt_core_news_sm
from elasticsearch import Elasticsearch

from fastapi import FastAPI

from politiquices.extraction.utils import clean_title

app = FastAPI()

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, "../classifiers/news_titles/trained_models/")
RESOURCES = os.path.join(APP_ROOT, "resources/")

print("Loading spaCy model...")
nlp = pt_core_news_sm.load(disable=["tagger", "parser"])

# ToDo: fail on error
print("Setting up connection with Elasticsearch")
es = Elasticsearch([{"host": "localhost", "port": 9200}])

print("Loading trained models...")
relationship_clf = joblib.load(MODELS + "relationship_clf_2020-10-11_140818.pkl")
relevancy_clf = joblib.load(MODELS + "relevancy_clf_2020-10-10_211240.pkl")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/relevant")
async def classify_relevancy(news_title: Optional[str] = None):
    title = clean_title(news_title).strip()
    predicted_probs = relevancy_clf.tag(title)
    return {
        label: float(pred)
        for label, pred in zip(relevancy_clf.label_encoder.classes_, predicted_probs[0])
    }


@app.get("/named_entities")
async def named_entities(news_title: Optional[str] = None):
    title = clean_title(news_title).strip()
    doc = nlp(title)
    entities = {ent.text: ent.label_ for ent in doc.ents}
    persons_to_tag = ['Marcelo', 'Passos', 'Rio']
    persons = []

    for k, v in entities.items():
        if k in persons_to_tag and v != 'PER':
            persons.append(k)
        if v == 'PER':
            persons.append(k)

    return persons


@app.get("/relationship/")
async def classify_relationship(news_title: Optional[str] = None):
    title = clean_title(news_title).strip()
    persons = await named_entities(title)
    if len(persons) < 2:
        # ToDo: if no persons are found try string matching with wikidata ?
        return {"not enough entities": persons}
    if len(persons) > 2:
        # ToDo: extract all possible contexts
        return {"more than 2 entities": persons}

    title = title.replace(persons[0], "PER").replace(persons[1], "PER")
    predicted_probs = relationship_clf.tag([title])

    rel_type_scores = {
        label: float(pred)
        for label, pred in zip(relationship_clf.label_encoder.classes_, predicted_probs[0])
    }

    result = {
        "entity_1": persons[0],
        "entity_2": persons[1],
    }

    wiki_id_1 = None
    wiki_id_2 = None

    try:
        wiki_id_1 = await wikidata_linking(persons[0])
        wiki_id_2 = await wikidata_linking(persons[1])

    except Exception as e:
        print(type(e))
        print(e)
        # ToDo: all type of errors
        # e.g: RequestError(400, 'search_phase_execution_exception',
        # 'Failed to parse query [Fernando AND Gomes AND  AND Lusa]')

    if wiki_id_1 and wiki_id_2:
        result.update({"entity_1_wiki": wiki_id_1["wiki_id"],
                       "entity_2_wiki": wiki_id_2["wiki_id"]})
    else:
        result.update({"entity_1_wiki": None,
                       "entity_2_wiki": None})
    return {**rel_type_scores, **result}


@app.get("/wikidata")
async def wikidata_linking(entity: str):

    # ToDo: handle this in indexing
    mappings = {
        "Costa": "António Costa",
        "Durão": "Durão Barroso",
        "Ferreira de o Amaral": "Joaquim Ferreira do Amaral",
        "Jerónimo": "Jerónimo de Sousa",
        "Nobre": "Fernando Nobre",
        "Marques Mendes": "Luís Marques Mendes",
        "Marcelo": "Marcelo Rebelo de Sousa",
        "Rebelo de Sousa": "Marcelo Rebelo de Sousa",
        "Carrilho": "Manuela Maria Carrilho",
        "Menezes": "Luís Filipe Menezes",
        "Moura Guedes": "Manuela Moura Guedes",
        "Portas": "Paulo Portas",
        "Relvas": "Miguel Relvas",
        "Soares": "Mário Soares",
        "Sousa Tavares": "Miguel Sousa Tavares",
        "Santos Silva": "Augusto Santos Silva",
        "Santana": "Pedro Santana Lopes",
    }

    entity_clean = re.sub(r'[:-]', '', entity)
    entity_clean = re.sub(r'\s+', ' ', entity_clean)
    entity_clean = mappings.get(entity, entity_clean)
    entity_query = " AND ".join(entity_clean.strip().split(' '))
    res = es.search(index="politicians", body={"query": {"query_string": {"query": entity_query}}})

    if res["hits"]["hits"]:
        return {"wiki_id": res["hits"]["hits"][0]["_source"]}

    return {"wiki_id": None}
