import os
from typing import Optional, List

import pickle
import pt_core_news_lg
from elasticsearch import Elasticsearch

from fastapi import FastAPI, Query

from keras.models import load_model

from politiquices.classifiers.news_titles.relationship_direction_clf import detect_direction
from politiquices.extraction.utils.utils import clean_title_re
from politiquices.extraction.utils.utils import clean_title_quotes
from politiquices.classifiers.news_titles.models.relationship_clf import Attention

app = FastAPI()

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, "../classifiers/news_titles/trained_models/")
RESOURCES = os.path.join(APP_ROOT, "resources/")

print("Loading spaCy model...")
nlp_core = pt_core_news_lg.load(disable=["parser"])

# ToDo: fail on error
print("Setting up connection with Elasticsearch")
es = Elasticsearch([{"host": "localhost", "port": 9200}])


print("Loading trained models...")

with open(MODELS + 'relationship_clf_2020-11-08_171703.pkl', 'rb') as f_in:
    relationship_clf = pickle.load(f_in)
model = load_model(
    MODELS + 'relationship_clf_2020-11-08_171703.h5',
    custom_objects={"Attention": Attention}
)
relationship_clf.model = model


with open(MODELS + 'relevancy_clf_2020-11-08_163340.pkl', 'rb') as f_in:
    relevancy_clf = pickle.load(f_in)
model = load_model(
    MODELS + 'relevancy_clf_2020-11-08_163340.h5',
    custom_objects={"Attention": Attention}
)
relevancy_clf.model = model


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/ner")
async def named_entities(news_title: Optional[str] = None):
    title = clean_title_quotes(clean_title_re(news_title).strip())
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


@app.get("/relevancy")
async def classify_relevancy(news_title: str, person: List[str] = Query(None)):
    persons = person
    title = clean_title_quotes((clean_title_re(news_title))).strip()

    # if persons are given replace them by 'PER'
    if persons:
        if len(persons) < 2:
            return {"not enough entities": person}

        if len(persons) > 2:
            return {"more than 2 entities": person}

        title = title.replace(persons[0].strip(), "PER").replace(persons[1].strip(), "PER")

    predicted_probs = relevancy_clf.tag([title], log=True)

    rel_type_scores = {
        label: float(pred)
        for label, pred in zip(relevancy_clf.label_encoder.classes_, predicted_probs[0])
    }

    rel_type_scores['original'] = news_title
    rel_type_scores['clean'] = title

    return rel_type_scores


@app.get("/relationship")
async def classify_relationship(news_title: str, person: List[str] = Query(None)):
    persons = person
    title = clean_title_quotes((clean_title_re(news_title))).strip()

    if len(persons) < 2:
        return {"not enough entities": person}

    if len(persons) > 2:
        return {"more than 2 entities": person}

    # ToDo: discard PER e PER -> classify as other automatically

    title = title.replace(persons[0].strip(), "PER").replace(persons[1].strip(), "PER")
    predicted_probs = relationship_clf.tag([title], log=True)

    rel_type_scores = {
        label: float(pred)
        for label, pred in zip(relationship_clf.label_encoder.classes_, predicted_probs[0])
    }

    rel_type_scores['original'] = news_title
    rel_type_scores['clean'] = title

    return rel_type_scores


@app.get("/direction")
async def classify_direction(news_title: str, person: List[str] = Query(None)):
    clean_title = clean_title_quotes(clean_title_re(news_title))
    doc = nlp_core(clean_title)
    persons = person
    ent1 = persons[0]
    ent2 = persons[1]

    if ent1 not in clean_title or ent2 not in clean_title:
        return {'no entities found': clean_title,
                'ent1': ent1,
                'ent2': ent2}

    pos_tags = [(t.text, t.pos_, t.tag_) for t in doc]
    pred, pattern = detect_direction(pos_tags, ent1, ent2)

    return {'direction': pred,
            'original': news_title,
            'clean': clean_title.replace(persons[0].strip(), "PER").replace(persons[1].strip(), "PER")
            }


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


@app.get("/all")
async def full_pipeline(news_title: str, person: List[str] = Query(None)):
    relevancy = await classify_relevancy(news_title, person)
    relationship = await classify_relationship(news_title, person)
    direction = await classify_direction(news_title, person)

    return {
        'relevancy': relevancy,
        'relationship': relationship,
        'direction': direction,

    }
