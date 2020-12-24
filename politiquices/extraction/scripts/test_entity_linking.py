import json
import argparse
import jsonlines

from politiquices.extraction.classifiers.entity_linking.entitly_linking_clf import entity_linking
from politiquices.extraction.classifiers.ner.rule_based_ner import RuleBasedNer
from politiquices.extraction.utils.utils import clean_title_quotes, clean_title_re


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publico", help="input is publico.pt crawled titles")
    parser.add_argument("--arquivo", help="input is from arquivo.pt API")
    parser.add_argument("--chave", help="input is from Linguateca CHAVE collection")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    # set up the NER system
    rule_ner = RuleBasedNer()

    # load named-entities that should be ignored
    with open('ner_ignore.txt', 'rt') as f_in:
        ner_ignore = [line.strip() for line in f_in.readlines()]

    if args.publico:
        f_name = args.publico
    elif args.arquivo:
        f_name = args.arquivo
    elif args.chave:
        f_name = args.chave

    ner_linked = jsonlines.open("ner_linked.jsonl", mode="w")
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
                entity1_candidates = entity_linking(persons[0], all_results=True)
                entity2_candidates = entity_linking(persons[1], all_results=True)

                if len(entity1_candidates) > 1 or len(entity2_candidates) > 1:
                    print(cleaned_title)
                    print(url)
                    print(persons[0], len(entity1_candidates))
                    for e in entity1_candidates:
                        print(e)
                        print(e['_score'], e['_source'])
                    print(persons[1], len(entity2_candidates))
                    for e in entity2_candidates:
                        print(e['_score'], e['_source'])
                    print()

                if len(persons[0].split()) == 1 or len(persons[1].split()) == 1:
                    print(cleaned_title)
                    print(url)
                    print(persons[0], len(entity1_candidates))
                    for e in entity1_candidates:
                        print(e['_score'], e['_source'])
                    print(persons[1], len(entity2_candidates))
                    for e in entity2_candidates:
                        print(e['_score'], e['_source'])
                    print()


if __name__ == "__main__":
    main()
