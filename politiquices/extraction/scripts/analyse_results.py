import sys
from collections import Counter, defaultdict

import jsonlines


def titles_processed(f_name):
    with jsonlines.open(f_name, 'r') as f_in:
        for entry in f_in:
            print(entry['title'])


def titles_no_entities():
    # ToDo: see top n-grams: 1 to 3 for capitalized tokens
    # with jsonlines.open('titles_processed_no_entities.jsonl', 'r') as f_in:
    pass


def entities_no_wiki_link():
    with jsonlines.open('titles_processed_no_wiki_id.jsonl', 'r') as f_in:
        no_wiki_link = []
        for entry in f_in:
            if entry['ent_1'] is None:
                no_wiki_link.append(entry['entities'][0])
            if entry['ent_2'] is None:
                no_wiki_link.append(entry['entities'][1])
    return Counter(no_wiki_link)


def entities_no_relation():
    with jsonlines.open('titles_processed_no_relation.jsonl', 'r') as f_in:
        no_relation_pairs_titles = defaultdict(list)
        no_relation_pairs_count = []

        for entry in f_in:
            ent_1 = entry['entities'][0]
            ent_2 = entry['entities'][1]
            pair = str(ent_1+' <-> '+ent_2)
            no_relation_pairs_count.append(pair)
            no_relation_pairs_titles[pair].append(entry['title'])

    return Counter(no_relation_pairs_count), Counter(no_relation_pairs_titles)


def main():
    """
    no_wiki_link = entities_no_wiki_link()
    for el in no_wiki_link.most_common():
        print(el)
    """

    titles_processed(sys.argv[1])

    """
    no_relation_pairs_count, no_relation_pairs_titles = entities_no_relation()
    for el in no_relation_pairs_count.most_common():
        print(el)

    for el in no_relation_pairs_count.most_common(10):
        print(el[0])
        for title in no_relation_pairs_titles[el[0]]:
            print(title)
            print()
        print("\n\n---------------------")
    """


if __name__ == '__main__':
    main()
