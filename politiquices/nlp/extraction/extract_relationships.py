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
    with open('../classifiers/ner/names_phrase_patterns.txt', 'rt') as f_in:
        names_phrase_patterns = [line.strip() for line in f_in]
    with open('../classifiers/ner/names_token_patterns.txt', 'rt') as f_in:
        names_token_patterns = [line.strip() for line in f_in]
    return RuleBasedNer(names_token_patterns, names_phrase_patterns)


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
    relationship_clf = joblib.load(MODELS + "latest")

    print("Loading NER classifier")
    ner = get_ner()
    # ToDo: load named-entities that should be ignored in the NER model itself
    with open('../classifiers/ner/names_ignore.txt', 'rt') as f_in:
        ner_ignore = [line.strip() for line in f_in.readlines()]

    # print("Loading relation direction classifier")
    direction_clf = DirectionClassifier()

    print("Loading Entity Linking")
    articles_db = ArticlesDB()
    el = EntityLinking(ner, articles_db)

    # log everything for error analysis
    ner_ignored = jsonlines.open("ner_ignored.jsonl", mode="w")
    no_entities = jsonlines.open("titles_processed_no_entities.jsonl", mode="w")
    more_entities = jsonlines.open("titles_processed_more_entities.jsonl", mode="w")
    no_wiki = jsonlines.open("titles_processed_no_wiki_id.jsonl", mode="w")
    processed = jsonlines.open("titles_processed.jsonl", mode="w")
    ner_linked = jsonlines.open("ner_linked.jsonl", mode="w")

    count = 0

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
            title_PER = cleaned_title.replace(persons[0], "PER").replace(persons[1], "PER")

            # detect relationship direction
            pred, pattern = direction_clf.detect_direction(cleaned_title, persons[0], persons[1])

            predicted_probs = relationship_clf.tag([title_PER])
            rel_type_scores = {
                label: float(pred)
                for label, pred in zip(
                    relationship_clf.label_encoder.classes_, predicted_probs[0]
                )
            }

            new_scores = dict()
            for k, v in rel_type_scores.items():
                predicted = pred.replace('rel', k)
                new_scores[predicted] = v

            result = {
                "title": cleaned_title,
                "entities": persons,
                "ent_1": entity1_wiki,
                "ent_2": entity2_wiki,
                "scores": new_scores,
                "url": url,
                "date": date,
            }

            if entity1_wiki is None or entity2_wiki is None:
                no_wiki.write(result)
            else:
                processed.write(result)

            ner_linked.write({"ner": persons[0], "wiki": result['ent_1'], "url": url})
            ner_linked.write({"ner": persons[1], "wiki": result['ent_2'], "url": url})


if __name__ == "__main__":
    main()
