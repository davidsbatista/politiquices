import os
import json
import argparse

import joblib
import jsonlines

from politiquices.nlp.data_sources.articles_db import ArticlesDB
from politiquices.nlp.classifiers.ner.rule_based_ner import RuleBasedNer
from politiquices.nlp.classifiers.direction.relationship_direction_clf import DirectionClassifier
from politiquices.nlp.classifiers.entity_linking.entitly_linking_clf import EntityLinking
from politiquices.nlp.utils.utils import clean_title_quotes, clean_title_re

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, "../classifiers/relationship/trained_models/")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publico", help="input is publico.pt crawled titles")
    parser.add_argument("--arquivo", help="input is from arquivo.pt API")
    parser.add_argument("--chave", help="input is from Linguateca CHAVE collection")
    args = parser.parse_args()
    if not any((args.chave, args.publico, args.arquivo)):
        print("Need to give at least one input")
        exit(-1)
    return args


def get_ner():
    # set up the custom NER system
    ner_full_path = os.path.join(APP_ROOT, '../classifiers/ner/')
    with open(ner_full_path+'/names_phrase_patterns.txt', 'rt') as f_in:
        names_phrase_patterns = [line.strip() for line in f_in]
    with open(ner_full_path+'/names_token_patterns.txt', 'rt') as f_in:
        names_token_patterns = [line.strip() for line in f_in]
    return RuleBasedNer(names_token_patterns, names_phrase_patterns)


def dummy_fun(doc):
    return doc


def main():
    args = parse_args()

    if args.publico:
        f_name = args.publico

    if args.chave:
        f_name = args.chave

    if args.arquivo:
        f_name = args.arquivo

    # load the relationships classification model
    print("Loading relationship classifier...")
    relationship_clf = joblib.load(MODELS + "SVC_2021_06_19_03_12.joblib")
    tf_idf_vectorizer = joblib.load(MODELS + "tf_idf_weights_2021_06_19_03_12.joblib")

    print("Loading NER classifier")
    ner = get_ner()
    # ToDo: load named-entities that should be ignored in the NER model itself
    with open('../classifiers/ner/names_ignore.txt', 'rt') as f_in:
        ner_ignore = [line.strip() for line in f_in.readlines()]

    print("Loading relation direction classifier")
    direction_clf = DirectionClassifier()

    print("Loading Entity Linking")
    articles_db = ArticlesDB()

    mappings = {
        "Cavaco": "Aníbal Cavaco Silva",
        "Marques Mendes": "Luís Marques Mendes",
    }

    el = EntityLinking(ner, articles_db, mappings)

    # log everything for error analysis
    ner_ignored = jsonlines.open("ner_ignored.jsonl", mode="w")
    no_entities = jsonlines.open("titles_processed_no_entities.jsonl", mode="w")
    more_entities = jsonlines.open("titles_processed_more_entities.jsonl", mode="w")
    processed = jsonlines.open("titles_processed.jsonl", mode="w")
    ner_linked = jsonlines.open("ner_linked.jsonl", mode="w")
    processing_errors = jsonlines.open("processing_errors.jsonl", mode="w")

    count = 0

    with open(f_name, 'rt') as f_in:

        for line in f_in:

            if args.publico:
                entry = line.split('\t')
                date = entry[0]
                url = entry[1]
                title = entry[2]

            elif args.arquivo or args.chave:
                print(line)
                entry = json.loads(line)
                title = entry["title"]
                url = entry["linkToArchive"]
                date = entry["tstamp"]

            count += 1
            if count % 1000 == 0:
                print(count)

            try:
                cleaned_title = clean_title_re(title)
            except Exception as e:
                print(e)
                print(title)
                continue

            # named-entity recognition
            persons = ner.tag(cleaned_title)

            # ignore certain 'person' entities
            # ToDo: move this to the ner object
            if any(person in persons for person in ner_ignore):
                ner_ignored.write({"title": cleaned_title, "entities": persons})
                continue

            if len(persons) <= 1:
                no_entities.write({"title": cleaned_title, "entities": persons})
                continue

            if len(persons) > 2:
                more_entities.write({"title": cleaned_title, "entities": persons})
                continue

            # entity linking
            entity1_wiki = el.entity_linking(persons[0], url)
            entity2_wiki = el.entity_linking(persons[1], url)

            # relationship extraction
            labels = ['opposes', 'other', 'supports']

            from politiquices.nlp.classifiers.relationship.train_clf_linear import get_text_tokens

            sample = {'title': cleaned_title, 'ent1': persons[0], 'ent2': persons[1]}

            try:
                textual_context = get_text_tokens([sample], tokenized=True)
            except TypeError:
                processing_errors.write(sample)
                continue

            tf_idf_weights = tf_idf_vectorizer.transform(textual_context)
            predicted_probs = relationship_clf.predict_proba(tf_idf_weights)
            rel_type_scores = {
                label: float(pred)
                for label, pred in zip(labels, predicted_probs[0])
            }

            pred_rel = max(rel_type_scores, key=rel_type_scores.get)

            if pred_rel != 'other':
                # detect relationship direction
                pred, pattern, context, pos_tags = direction_clf.detect_direction(
                    cleaned_title, persons[0], persons[1]
                )
                pred_rel = pred.replace("rel", pred_rel)

            result = {
                "title": cleaned_title,
                "entities": persons,
                "ent_1": entity1_wiki,
                "ent_2": entity2_wiki,
                "scores": rel_type_scores,
                "pred_rel": pred_rel,
                "url": url,
                "date": date,
            }

            if entity1_wiki and entity2_wiki:
                processed.write(result)

            ner_linked.write({"ner": persons[0], "wiki": result['ent_1'], "url": url})
            ner_linked.write({"ner": persons[1], "wiki": result['ent_2'], "url": url})


if __name__ == "__main__":
    main()
