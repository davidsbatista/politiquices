import jsonlines
from collections import defaultdict


def count_non_linked(entries):
    no_match = defaultdict(int)
    for e in entries:
        if e['wiki'] is None:
            no_match[e['ner']] += 1

    no_match_sorted = {k: v for k, v in sorted(no_match.items(), key=lambda x: x[1], reverse=True)}
    for k, v in no_match_sorted.items():
        print(k, v)


def main():
    with jsonlines.open('titles_processed_no_wiki_id.jsonl') as f_in:
        entries = list(f_in)

    for e in sorted(entries, key=lambda x: x['title']):
        print(e['title'])
        print(e['entities'])
        print()


if __name__ == '__main__':
    main()
