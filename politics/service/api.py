import os
from typing import Optional

import joblib
import pt_core_news_sm

from fastapi import FastAPI
from keras_preprocessing.sequence import pad_sequences
from keras.models import load_model

app = FastAPI()

print("Loading spaCy model...")
nlp = pt_core_news_sm.load(disable=["tagger", "parser"])

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, "../classifier/trained_models/")
RESOURCES = os.path.join(APP_ROOT, "resources/")

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.WARNING)

print("Loading trained models...")
clf = load_model(MODELS + "rel_clf_2020-07-18-01:07:12.h5")
word2index = joblib.load(MODELS + "word2index_2020-07-18-01:07:12.joblib")
le = joblib.load(MODELS + "label_encoder_2020-07-04-02:07:44.joblib")
with open(MODELS + "max_input_length", "rt") as f_in:
    max_input_length = int(f_in.read().strip())


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/relevant")
async def relevant_clf():
    # ToDo: call the relevant classifier to apply to news titles
    return {"message": "Hello World"}


@app.get("/relationship/")
async def relationship_clf(news_title: Optional[str] = None):
    # ToDo: if no context or context = 1 char return None
    # ToDo: logging ?

    doc = nlp(news_title)
    persons = [ent.text for ent in doc.ents if ent.label_ == "PER"]
    if len(persons) != 2:
        pass

    # replace entity name by 'PER'
    news_title_PER = news_title.replace(persons[0], "PER").replace(persons[1], "PER")

    word_no_vectors = set()
    tokens = [str(t).lower() for t in news_title_PER]
    x_vec = []

    for tok in tokens:
        if tok in word2index:
            x_vec.append(word2index[tok])
        else:
            x_vec.append(word2index["UNKNOWN"])
            word_no_vectors.add(tok)

    x_vec_padded = pad_sequences(
        [x_vec], maxlen=max_input_length, padding="post", truncating="post"
    )
    predicted_probs = clf.predict(x_vec_padded)[0]
    scores = {label: float(pred) for label, pred in zip(le.classes_, predicted_probs)}
    result = {
        "title": news_title,
        "entity_1": persons[0],
        "entity_2": persons[1],
        "entity_1_wiki": "wiki_1",
        "entity_2_wiki": "wiki_2",
    }

    return {**scores, **result}


@app.get("/items/")
async def read_items(q: Optional[str] = None):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@app.get("/wikidata")
async def wikidata_linking():
    # ToDo: call the relationship classifier to apply to a relevant title
    return {"message": "Hello World"}
