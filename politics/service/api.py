import os
from typing import Optional

import joblib
import pt_core_news_sm
from elasticsearch import Elasticsearch

from fastapi import FastAPI
from keras_preprocessing.sequence import pad_sequences
from keras.models import load_model

from politics.classifier.embeddings_utils import vectorize_titles

app = FastAPI()

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, "../classifier/trained_models/")
RESOURCES = os.path.join(APP_ROOT, "resources/")

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.WARNING)

print("Loading spaCy model...")
nlp = pt_core_news_sm.load(disable=["tagger", "parser"])

print("Setting up connection with Elasticsearch")
es = Elasticsearch([{"host": "localhost", "port": 9200}])

print("Loading trained models...")
relationship_word2index = joblib.load(MODELS + "relationship_word2index.joblib")
relationship_clf = load_model(MODELS + "relationship_clf.h5")
relationship_le = joblib.load(MODELS + "relationship_label_encoder.joblib")
with open(MODELS + "relationship_max_input_length", "rt") as f_in:
    relationship_input_length = int(f_in.read().strip())

relevancy_word2index = joblib.load(MODELS + "relevancy_word2index.joblib")
relevancy_clf = load_model(MODELS + "relevancy_clf.h5")
relevancy_le = joblib.load(MODELS + "relevancy_label_encoder.joblib")
with open(MODELS + "relevancy_max_input_length", "rt") as f_in:
    relevancy_input_length = int(f_in.read().strip())


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/relevant")
async def classify_relevancy(news_title: Optional[str] = None):
    x_test_vec = vectorize_titles(relevancy_word2index, [news_title])
    x_test_vec_padded = pad_sequences(
        x_test_vec, maxlen=relevancy_input_length, padding="post", truncating="post"
    )
    predicted_probs = relevancy_clf.predict(x_test_vec_padded)
    scores = {label: float(pred) for label, pred in zip(relevancy_le.classes_, predicted_probs[0])}

    return scores


@app.get("/relationship/")
async def classify_relationship(news_title: Optional[str] = None):
    doc = nlp(news_title)
    persons = [ent.text for ent in doc.ents if ent.label_ == "PER"]
    # ToDo: if no persons are found try string matching with wikidata ?
    if len(persons) != 2:
        return {'not enough entities': persons}
    news_title_PER = news_title.replace(persons[0], "PER").replace(persons[1], "PER")
    x_test_vec = vectorize_titles(relationship_word2index, [news_title_PER])
    x_test_vec_padded = pad_sequences(
        x_test_vec, maxlen=relationship_input_length, padding="post", truncating="post"
    )
    predicted_probs = relationship_clf.predict(x_test_vec_padded)
    scores = {label: float(pred) for label, pred in zip(relationship_le.classes_, predicted_probs[0])}
    wiki_id_1 = await wikidata_linking(persons[0])
    wiki_id_2 = await wikidata_linking(persons[1])
    result = {
        "title": news_title,
        "entity_1": persons[0],
        "entity_2": persons[1],
        "entity_1_wiki": wiki_id_1['wiki_id'],
        "entity_2_wiki": wiki_id_2['wiki_id'],
    }

    return {**scores, **result}


@app.get("/wikidata")
async def wikidata_linking(entity: str):
    # ToDo: handle this in indexing
    mappings = {
        'Costa': 'António Costa',
        'Durão': 'Durão Barroso',
        'Ferreira de o Amaral': 'Joaquim Ferreira do Amaral',
        'Jerónimo': 'Jerónimo de Sousa',
        'Nobre': 'Fernando Nobre',
        'Marques Mendes': 'Luís Marques Mendes',
        'Marcelo': 'Marcelo Rebelo de Sousa',
        'Rebelo de Sousa': 'Marcelo Rebelo de Sousa',
        'Carrilho': 'Manuela Maria Carrilho',
        'Menezes': 'Luís Filipe Menezes',
        'Moura Guedes': 'Manuela Moura Guedes',
        'Portas': 'Paulo Portas',
        'Relvas': 'Miguel Relvas',
        'Soares': 'Mário Soares',
        'Sousa Tavares': 'Miguel Sousa Tavares',
        'Santos Silva': 'Augusto Santos Silva',
        'Santana': 'Pedro Santana Lopes',

        # due to contractions
        'Adelino Amaro de a Costa': 'Adelino Amaro da Costa',
        'Amaro de a Costa': 'Amaro da Costa',
        'Carvalho de a Silva': 'Carvalho da Silva',
        'Gomes de a Silva': 'Gomes da Silva',
        'João César de as Neves': 'João César das Neves',
        'Rui Gomes de a Silva': 'Rui Gomes da Silva',
        'Martins de a Cruz': 'Martins da Cruz',
        'Manuel de os Santos': 'Manuel dos Santos',
        'Teixeira de os Santos': 'Teixeira dos Santos',
        'Freitas de o Amaral': 'Freitas do Amaral',
        'Moreira de a Silva': 'Moreira da Silva',
        'Paula Teixeira de a Cruz': 'Paula Teixeira da Cruz',
        'Vieira de a Silva': 'Vieira da Silva'
    }
    entity = mappings.get(entity, entity)
    entity_query = ' AND '.join(entity.split(' '))
    res = es.search(
        index="politicians", body={"query": {"query_string": {"query": entity_query}}}
    )
    if res['hits']['hits']:
        return {'wiki_id': res['hits']['hits'][0]['_source']}

    return {'wiki_id': None}
