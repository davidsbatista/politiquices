import os
import sys
import joblib
import requests
from jsonlines import jsonlines
import pt_core_news_sm

from politiquices.extraction.utils import clean_title

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, "../classifiers/news_titles/trained_models/")
RESOURCES = os.path.join(APP_ROOT, "resources/")

print("Loading relationship classifier...")
relationship_clf = joblib.load(MODELS + "relationship_clf_2020-10-17_001401.pkl")

url = "http://127.0.0.1:8000/wikidata"

nlp = pt_core_news_sm.load(disable=["tagger", "parser"])


def entity_linking(entity):
    payload = {'entity': entity}
    response = requests.request("GET", url, params=payload)
    return response.json()


def get_persons(title):
    doc = nlp(title)
    entities = {ent.text: ent.label_ for ent in doc.ents}
    persons_to_tag = ['Marcelo', 'Passos', 'Rio', 'Centeno', 'Negrão', 'Relvas', 'Costa',
                      'Coelho', 'Santana', 'Alegre', 'Sócrates']

    persons = []

    for k, v in entities.items():
        if k in persons_to_tag and v != 'PER':
            persons.append(k)
        if v == 'PER':
            persons.append(k)

    return persons


def main():
    processed = jsonlines.open('titles_processed.jsonl', mode='w')
    no_entities = jsonlines.open('titles_processed_no_entities.jsonl', mode='w')

    count = 0
    with jsonlines.open(sys.argv[1]) as f_in:
        for line in f_in:

            count += 1
            if count % 1000 == 0:
                print(count)

            cleaned_title = clean_title(line['title']).strip()
            persons = get_persons(cleaned_title)

            if len(persons) == 2:
                title_PER = cleaned_title.replace(persons[0], "PER").replace(persons[1], "PER")
                predicted_probs = relationship_clf.tag([title_PER])
                rel_type_scores = {
                    label: float(pred)
                    for label, pred in
                    zip(relationship_clf.label_encoder.classes_, predicted_probs[0])
                }

                # ToDo: gravar este scores também e ver o resultado
                if rel_type_scores['other'] > 0.5:
                    continue

                entity = entity_linking(persons[0])
                ent_1 = entity['wiki_id'] if entity['wiki_id'] else None
                entity = entity_linking(persons[1])
                ent_2 = entity['wiki_id'] if entity['wiki_id'] else None
                result = {
                    'title': cleaned_title,
                    'entities': persons,
                    'ent_1': ent_1,
                    'ent_2': ent_2,
                    'scores': rel_type_scores,
                    'linkToArchive': line['linkToArchive'],
                    'tstamp': line['tstamp']
                }
                processed.write(result)

            else:
                no_entities.write({'title': cleaned_title, 'entities': persons})

    processed.close()


if __name__ == '__main__':
    main()
