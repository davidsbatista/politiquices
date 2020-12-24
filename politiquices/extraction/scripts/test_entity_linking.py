import json
import argparse
from collections import defaultdict

import jsonlines

from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize

from politiquices.extraction.classifiers.entity_linking.entitly_linking_clf import entity_linking
from politiquices.extraction.classifiers.ner.rule_based_ner import RuleBasedNer
from politiquices.extraction.utils.utils import clean_title_quotes, clean_title_re
from politiquices.extraction.scripts.utils import get_text
from politiquices.extraction.scripts.prepare_for_extraction import title_keywords_ignore


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publico", help="input is publico.pt crawled titles")
    parser.add_argument("--arquivo", help="input is from arquivo.pt API")
    parser.add_argument("--chave", help="input is from Linguateca CHAVE collection")
    args = parser.parse_args()
    return args


def expand_entities(entity, text):
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
                print(end, end_idx)
                tks_aft = sentence_tokens[end:end_idx]
                aft = [tk for tk in tks_aft if tk.istitle()]
                if bef or aft:
                    expanded[' '.join(bef + entity_tokens + aft)] += 1

    return expanded


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

            if any(x in cleaned_title for x in title_keywords_ignore):
                continue

            # ToDo: before entity linking try to expand the named-entity
            if any(person in persons for person in ner_ignore):
                ner_ignored.write({"title": cleaned_title, "entities": persons})
                continue

            if len(persons) == 2:

                # entity linking
                entity1_candidates = entity_linking(persons[0], all_results=True)
                entity2_candidates = entity_linking(persons[1], all_results=True)

                if len(entity1_candidates) > 1:
                    print(url)
                    print(cleaned_title)
                    print(persons)
                    print(persons[0], len(entity1_candidates))
                    full_match_label = []
                    for e in entity1_candidates:
                        if e['label'] == persons[0]:
                            full_match_label.append(e)
                    if len(full_match_label) == 1:
                        print(full_match_label[0])
                    else:
                        text = get_text(url)
                        expanded_entity = expand_entities(persons[0], text)
                        print()
                        print(expanded_entity)
                    print("\n\n------------------")

                # NER
                # title_PER = cleaned_title.replace(persons[0], "PER").replace(persons[1], "PER")


if __name__ == "__main__":
    main()
