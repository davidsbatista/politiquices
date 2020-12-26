import json
import argparse
import os

import joblib
import jsonlines
from collections import defaultdict

import pt_core_news_lg
from nltk.tokenize import sent_tokenize, word_tokenize

from politiquices.extraction.classifiers.entity_linking.entitly_linking_clf import query_kb
from politiquices.extraction.classifiers.ner.rule_based_ner import RuleBasedNer
from politiquices.extraction.classifiers.news_titles.relationship_direction_clf import \
    detect_direction
from politiquices.extraction.utils.utils import clean_title_quotes, clean_title_re
from politiquices.extraction.scripts.utils import get_text_newspaper


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, "../classifiers/news_titles/trained_models/")
RESOURCES = os.path.join(APP_ROOT, "resources/")

# set up the custom NER system
rule_ner = RuleBasedNer()


def read_lstm_models():
    print("Loading relationship classifier...")
    relationship_clf = joblib.load(MODELS + "relationship_clf_2020-12-23_140325.pkl")
    return relationship_clf


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publico", help="input is publico.pt crawled titles")
    parser.add_argument("--arquivo", help="input is from arquivo.pt API")
    parser.add_argument("--chave", help="input is from Linguateca CHAVE collection")
    args = parser.parse_args()
    return args


def expand_entities_v1(entity, text):
    expanded = defaultdict(int)
    entity_tokens = word_tokenize(entity)
    for sentence in sent_tokenize(text, language='portuguese'):
        if entity in sentence:
            sentence_tokens = word_tokenize(sentence)
            print(sentence, len(sentence_tokens))
            matched_idx = [(i, i + len(entity_tokens))
                           for i in range(len(sentence_tokens))
                           if sentence_tokens[i:i + len(entity_tokens)] == entity_tokens]
            for matched_pair in matched_idx:
                start = matched_pair[0]
                end = matched_pair[1]
                start_idx = 0 if start <= 2 else start-2
                tks_bef = sentence_tokens[start_idx:start]
                bef = [tk for tk in tks_bef if tk.istitle() and tk]
                end_idx = len(sentence_tokens) if end >= len(sentence_tokens) - 2 else end + 2
                tks_aft = sentence_tokens[end:end_idx]
                aft = [tk for tk in tks_aft if tk.istitle()]
                if bef or aft:
                    expanded[' '.join(bef + entity_tokens + aft)] += 1

    return expanded


def expand_entities_v2(entity, text):
    all_entities, persons = rule_ner.tag(text)
    expanded = [p for p in persons if entity in p and entity != p]
    return expanded


def filter_perfect_matches(entity, candidates):
    # filter only for those whose label or aliases are a perfect match
    matches = []
    for c in candidates:
        if entity == c['label']:
            matches.append(c)
        else:
            if 'aliases' in c and c['aliases'] is not None:
                for alias in c['aliases']:
                    if entity == alias:
                        matches.append(c)

    return matches


def entity_linking(entity, url):

    candidates = query_kb(entity, all_results=True)
    no_wiki = jsonlines.open('no_wiki_id.jsonl', 'a')

    if len(candidates) == 1:
        return candidates[0]

    if len(candidates) > 1:
        full_match_label = filter_perfect_matches(entity.strip(), candidates)
        if len(full_match_label) == 1:
            return full_match_label[0]

        else:
            text = get_text_newspaper(url)
            expanded_entity = expand_entities_v2(entity, text)
            if len(expanded_entity) == 0:
                no_wiki.write({"entity": entity, "expanded": expanded_entity, "url": url})
                return None

            if len(expanded_entity) == 1:
                full_match_label = filter_perfect_matches(expanded_entity[0], candidates)
                if len(full_match_label) == 1:
                    return full_match_label[0]
                else:
                    # ToDo: make new query
                    """
                    print(url)
                    print(entity)
                    print("case 2 -> ", expanded_entity)
                    for e in candidates:
                        print(e)
                    """
                    no_wiki.write({"entity": entity, "expanded": expanded_entity, "url": url})
                    return None

            if len(expanded_entity) > 1:
                # ToDo: try to merge/disambiguate further
                if len(expanded_entity) == 2:
                    new_entity = None
                    if expanded_entity[0] in expanded_entity[1]:
                        new_entity = expanded_entity[1]
                    if expanded_entity[1] in expanded_entity[0]:
                        new_entity = expanded_entity[0]
                    full_match_label = filter_perfect_matches(new_entity, candidates)
                    if len(full_match_label) == 1:
                        return full_match_label[0]

                # print(url)
                # print(entity)
                # print("case 3 -> ", expanded_entity, len(expanded_entity))
                # for e in candidates:
                #   print(e)
                no_wiki.write({"entity": entity, "expanded": expanded_entity, "url": url})
                return None

    else:
        no_wiki.write({"entity": entity, "expanded": 'no_candidates', "url": url})
        return None


def main():
    args = parse_args()

    # load named-entities that should be ignored
    with open('ner_ignore.txt', 'rt') as f_in:
        ner_ignore = [line.strip() for line in f_in.readlines()]

    if args.publico:
        f_name = args.publico
    elif args.arquivo:
        f_name = args.arquivo
    elif args.chave:
        f_name = args.chave
    else:
        print(args)
        exit(-1)

    # load the relationships classification model
    relationship_clf = read_lstm_models()

    # use spaCy models to extract title morphological information
    print("Loading spaCy NLP model")
    nlp = pt_core_news_lg.load()
    nlp.disable = ["tagger", "parser", "ner"]

    # open files for logging and later diagnostic
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
            all_entities, persons = rule_ner.tag(cleaned_title)

            # ignore certain 'person' entities
            if any(person in persons for person in ner_ignore):
                ner_ignored.write({"title": cleaned_title, "entities": persons})
                continue

            if len(persons) == 2:

                # entity linking
                entity1_wiki = entity_linking(persons[0], url)
                entity2_wiki = entity_linking(persons[1], url)

                # relationship extraction
                title_PER = cleaned_title.replace(persons[0], "PER").replace(persons[1], "PER")

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

            elif len(persons) > 2:
                more_entities.write({"title": cleaned_title, "entities": persons})

            else:
                no_entities.write({"title": cleaned_title, "entities": persons})


if __name__ == "__main__":
    main()
