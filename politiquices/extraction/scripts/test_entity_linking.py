import json
import argparse

import jsonlines

from politiquices.extraction.classifiers.entity_linking.entitly_linking_clf import query_kb
from politiquices.extraction.classifiers.ner.rule_based_ner import RuleBasedNer
from politiquices.extraction.utils.utils import clean_title_quotes, clean_title_re
from politiquices.extraction.scripts.utils import get_text_newspaper


# set up the custom NER system
rule_ner = RuleBasedNer()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publico", help="input is publico.pt crawled titles")
    parser.add_argument("--arquivo", help="input is from arquivo.pt API")
    parser.add_argument("--chave", help="input is from Linguateca CHAVE collection")
    args = parser.parse_args()
    return args


def expand_entities_v2(entity, text):
    all_entities, persons = rule_ner.tag(text)
    expanded = [p for p in persons if entity in p and entity != p]
    return expanded


def filter_perfect_matches(entity, candidates):
    # filter only for those whose label or aliases are a perfect match

    # ToDo: clean entity
    clean = ['dr.', 'sr.']

    matches = []
    for c in candidates:
        if entity == c['label']:
            return [c]
        else:
            if 'aliases' in c and c['aliases'] is not None:
                for alias in c['aliases']:
                    print(entity.lower(), alias.lower())
                    print(entity.lower() == alias.lower())
                    if entity.lower() == alias.lower():
                        return [c]

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
                    candidates = query_kb(expanded_entity[0], all_results=True)
                    full_match_label = filter_perfect_matches(expanded_entity[0], candidates)
                    print(full_match_label)
                    if len(full_match_label) == 1:
                        return full_match_label[0]
                    print('\n'+url)
                    print(entity)
                    print("case 2 -> ", expanded_entity)
                    for e in candidates:
                        print(e)
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
                    if new_entity:
                        full_match_label = filter_perfect_matches(new_entity, candidates)
                        if len(full_match_label) == 1:
                            return full_match_label[0]

                print('\n'+url)
                print(entity)
                print("case 3 -> ", expanded_entity, len(expanded_entity))
                for e in candidates:
                    print(e)
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

    # open files for logging and later diagnostic
    ner_ignored = jsonlines.open("ner_ignored.jsonl", mode="w")

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


if __name__ == "__main__":
    main()
