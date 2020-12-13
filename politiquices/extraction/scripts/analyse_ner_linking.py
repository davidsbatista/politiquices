import jsonlines
from collections import defaultdict

from politiquices.extraction.scripts.extract_relationships_v2 import entity_linking


def count_non_linked(entries):
    no_match = defaultdict(int)
    for e in entries:
        if e['wiki'] is None:
            no_match[e['ner']] += 1

    no_match_sorted = {k: v for k, v in sorted(no_match.items(), key=lambda x: x[1], reverse=True)}
    for k, v in no_match_sorted.items():
        print(k, v)


def see_highly_ambiguous(entries):
    with open('ner_ignore.txt', 'rt') as f_in:
        ner_ignore = [line.strip() for line in f_in.readlines()]
    seen = set()
    matches = defaultdict(dict)
    for e in entries:
        if e['wiki']:
            if e['ner'] in seen or e['ner'] in ner_ignore:
                continue
            entity = e['ner']
            if len(entity.split()) == 2:
                results = entity_linking(entity, all_results=True)
                matches[entity]['wiki'] = e['wiki']['wiki']
                matches[entity]['label'] = e['wiki']['label']
                matches[entity]['freq'] = len(results)
                seen.add(entity)


def main():
    with jsonlines.open('ner_linked.jsonl') as f_in:
        entries = list(f_in)
    # count_non_linked(entries)
    see_highly_ambiguous(entries)


if __name__ == '__main__':
    main()
