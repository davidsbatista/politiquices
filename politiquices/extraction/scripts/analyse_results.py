from collections import Counter, defaultdict

import jsonlines


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
            no_relation_pairs_count.append(ent_1+' <-> '+ent_2)
            no_relation_pairs_titles[ent_1+' <-> '+ent_2].append(entry['title'])

    return Counter(no_relation_pairs_count), Counter(no_relation_pairs_titles)


def main():
    """
    no_wiki_link = entities_no_wiki_link()
    for el in no_wiki_link.most_common():
        print(el)
    """

    no_relation_entities, no_relation_pairs = entities_no_relation()

    """
    for el in no_relation_entities.most_common():
        print(el)
    """

    for el in no_relation_pairs.most_common():
        print(el)


if __name__ == '__main__':
    main()
