import json
import os
import argparse
import joblib
import pickle

from jsonlines import jsonlines
from keras.models import load_model

from politiquices.extraction.classifiers.entity_linking.entitly_linking_clf import query_kb
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


def read_lstm_models():
    print("Loading relationship classifier...")
    relationship_clf = joblib.load(MODELS + "relationship_clf_2020-12-23_140325.pkl")
    return relationship_clf


def read_att_normal_models():
    print("Loading relationship classifier...")
    with open(MODELS + "relationship_clf_2020-12-05_164644.pkl", "rb") as f_in:
        relationship_clf = pickle.load(f_in)
    model = load_model(
        MODELS + "relationship_clf_2020-12-05_164644.h5", custom_objects={"Attention": Attention}
    )
    relationship_clf.model = model

    return relationship_clf, None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publico", help="input is publico.pt crawled titles")
    parser.add_argument("--arquivo", help="input is from arquivo.pt API")
    parser.add_argument("--chave", help="input is from Linguateca CHAVE collection")
    args = parser.parse_args()
    return args


def extract(args):
    # set up the NER system
    rule_ner = RuleBasedNer()

    # load named-entities that should be ignored
    with open('ner_ignore.txt', 'rt') as f_in:
        ner_ignore = [line.strip() for line in f_in.readlines()]

    # relationship_clf, relevancy_clf = read_avg_weighted_att_models()
    # relationship_clf, relevancy_clf = read_att_normal_models()
    relationship_clf = read_lstm_models()

    # open files for logging and later diagnostic
    no_entities = jsonlines.open("titles_processed_no_entities.jsonl", mode="w")
    more_entities = jsonlines.open("titles_processed_more_entities.jsonl", mode="w")
    no_wiki = jsonlines.open("titles_processed_no_wiki_id.jsonl", mode="w")
    processed = jsonlines.open("titles_processed.jsonl", mode="w")
    ner_linked = jsonlines.open("ner_linked.jsonl", mode="w")
    ner_ignored = jsonlines.open("ner_ignored.jsonl", mode="w")

    count = 0

    if args.publico:
        f_name = args.publico
    elif args.arquivo:
        f_name = args.arquivo
    elif args.chave:
        f_name = args.chave

    with open(f_name, 'rt') as f_in:
        for line in f_in:
            if args.publico:
                entry = line.split('\t')
                date = entry[0]
                url = entry[1]
                title = entry[2]

            elif args.arquivo or args.chave:
                entry = json.loads(line)
                title = entry["title"]
                url = entry["linkToArchive"]
                date = entry["tstamp"]

            count += 1
            if count % 1000 == 0:
                print(count)

            cleaned_title = clean_title_quotes(clean_title_re(title))
            all_entities, persons = rule_ner.tag(cleaned_title)

            # ToDo: before entity linking try to expand the named-entity
            if any(person in persons for person in ner_ignore):
                ner_ignored.write({"title": cleaned_title, "entities": persons})
                continue

            if len(persons) == 2:

                # NER
                title_PER = cleaned_title.replace(persons[0], "PER").replace(persons[1], "PER")

                # ToDo: before entity linking try to expand the named-entity
                # https://arquivo.pt/textextracted?m=<original_url>/<crawl_date>

                # entity linking
                entity1_candidates = query_kb(persons[0], all_results=True)
                print(persons[0], len(entity1_candidates))
                entity2_candidates = query_kb(persons[1], all_results=True)
                print(persons[1], len(entity1_candidates))

                ent_1 = entity["wiki_id"] if entity["wiki_id"] else None
                entity = query_kb(persons[1])
                ent_2 = entity["wiki_id"] if entity["wiki_id"] else None
                print(query_kb.cache_info())

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
                    "url": url,
                    "date": date,
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


def main():
    args = parse_args()
    extract(args)


if __name__ == "__main__":
    main()
