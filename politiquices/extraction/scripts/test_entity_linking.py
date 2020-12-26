import re
import json
import difflib
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


def clean_entity(entity):
    rep = {
        "Sr.": "",
        "[": "",
        "”": "",
        "doutor": "",
        "dr.": "",
        "Dr.": "",
        "sr.": "",
        "Foto": "",
        "Parabéns": "",
    }

    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))
    new_entity = pattern.sub(lambda m: rep[re.escape(m.group(0))], entity)

    return new_entity.strip()


def deburr_entity():
    pass
    # ToDo:
    # without dashes and ANSI version of a string


def expand_entities(entity, text):
    all_entities, persons = rule_ner.tag(text)
    expanded = [p for p in persons if entity in p and entity != p]
    expanded_clean = [clean_entity(x) for x in expanded]
    return merge_substrings(expanded_clean)


def find_perfect_match(entity, candidates):

    # filter only for those whose label or aliases are a perfect match
    matches = []
    for c in candidates:
        if entity == c['label']:
            return [c]
        else:
            if 'aliases' in c and c['aliases'] is not None:
                for alias in c['aliases']:
                    if entity.lower() == alias.lower():
                        return [c]
    return matches


def merge_substrings(entities):
    """
    This function eliminates entities which are already substrings of other  entities.

    This is based on the principle that if a polysemous word appears two or more times in a
    written discourse, it is extremely likely that they will all share the same sense.
    (see: https://www.aclweb.org/anthology/H92-1045.pdf)
    """

    # ToDo:
    # result = merge_substrings(['Jaime Gama', 'Jaime de Gama'])
    # assert result == ['Jaime Gama']

    # result = merge_substrings(['Paulo Azevedo', 'Paulo de Azevedo'])
    # assert result == ['Paulo de Azevedo']

    # result = merge_substrings(['Jose da Silva Lopes', 'José da Silva Lopes'])
    # assert result == ['José da Silva Lopes']

    # result = merge_substrings(["Guilherme d'Oliveira Martins", "Guilherme d' Oliveira Martins"])
    # assert result == ['Guilherme d'Oliveira Martins']

    new_entities = []

    # sort the locations by size
    entities_sorted = sorted([clean_entity(x) for x in entities], key=len)

    # starting with the shortest one see if it's a substring of any of the longer ones
    for idx, x in enumerate(entities_sorted):
        found = False
        for other in entities_sorted[idx + 1:]:
            if x in other:
                found = True
                break
        if not found and x not in new_entities:
            new_entities.append(x)

    return new_entities


def disambiguate(expanded_entities, candidates):

    """
    - several expanded entities
    - if more than 'threshold' of expanded entities match full with a candiadate return that
      candidate

    case 3 ->  ['Joe Berardo', 'José Berardo'] 2
    {'wiki': 'Q3186200', 'label': 'José Manuel Rodrigues Berardo', 'aliases': ['Joe Berardo',
    'Joe berardo', 'José berardo', 'José Berardo', 'José manuel rodrigues berardo',
    'Colecção Berardo']}

    case 3 ->  ['Joe Berardo', 'José Berardo', 'Coleção Berardo', 'Berardo um Acordo Quadro',
    'José Manuel Rodrigues Berardo']


    - just one expanded entity but two candidates
    case 2 ->  ['Filipe Menezes']
    {'wiki': 'Q6706787', 'last_modified': '2020-12-01T22:53:40Z', 'label': 'Luís Filipe Menezes',
    aliases': ['Luís Filipe Meneses', 'Luis Filipe de Menezes', 'Luís Filipe de Menezes']}
    {'wiki': 'Q10321558', 'last_modified': '2020-02-05T21:22:25Z', 'label': 'Luís Menezes',
    'aliases': ['Luís de Menezes', 'Luís Filipe Valenzuela Tavares de Menezes Lopes']}
    """

    def full_match_candidate(entities, candidate):
        matched = 0
        for ent in expanded_entities:
            matched += len(find_perfect_match(ent, [candidate]))
        return matched == len(entities)

    matching_candidates = [c for c in candidates if full_match_candidate(expanded_entities, c)]

    return matching_candidates


def fuzzy_match(entity, candidate, threshold=0.77):

    def fuzzy_compare(a, b):
        seq = difflib.SequenceMatcher(None, a, b)
        return seq.ratio()

    if fuzzy_compare(entity, candidate['label']) > threshold:
        return True

    if 'aliases' in candidate and candidate['aliases'] is not None:
        for alias in candidate['aliases']:
            if fuzzy_compare(entity, alias) > threshold:
                return True

    return False


def entity_linking(entity, url):
    candidates = query_kb(entity, all_results=True)
    no_wiki = jsonlines.open('no_wiki_id.jsonl', 'a')

    if len(candidates) == 0:
        no_wiki.write({"entity": entity, "expanded": 'no_candidates', "url": url})
        return None

    if len(candidates) == 1:
        # ToDo: how many false positives does this generates?
        return candidates[0]

    if len(candidates) > 1:
        full_match_label = find_perfect_match(entity.strip(), candidates)
        if len(full_match_label) == 1:
            return full_match_label[0]

    # try to expand named-entity based on article's complete text
    text = get_text_newspaper(url)
    expanded_entity = expand_entities(entity, text)

    if len(expanded_entity) == 0:
        no_wiki.write({"entity": entity, "expanded": expanded_entity, "url": url})
        return None

    if len(expanded_entity) == 1:
        full_match_label = find_perfect_match(expanded_entity[0], candidates)

        if len(full_match_label) == 1:
            return full_match_label[0]

        if len(candidates) == 1:
            if fuzzy_match(expanded_entity[0], candidates[0]):
                return candidates[0]

        # use expanded entity to issue a new query
        # ToDo: call new function?
        candidates = query_kb(expanded_entity[0], all_results=True)

        if len(candidates) == 0:
            no_wiki.write({"entity": entity, "expanded": 'no_candidates', "url": url})
            return None

        full_match_label = find_perfect_match(expanded_entity[0], candidates)
        if len(full_match_label) == 1:
            return full_match_label[0]

        if len(candidates) == 1:
            if fuzzy_match(expanded_entity[0], candidates[0]):
                return candidates[0]

        print('\n'+url)
        print(entity)
        print("case 2 -> ", expanded_entity)
        for e in candidates:
            print(e)
        no_wiki.write({"entity": entity, "expanded": expanded_entity, "url": url})
        return None

    if len(expanded_entity) > 1:
        matches = disambiguate(expanded_entity, candidates)
        if len(matches) == 1:
            return matches[0]
        print('\n' + url)
        print(entity)
        print("case 3 -> ", expanded_entity, len(expanded_entity))
        for e in candidates:
            print(e)
        no_wiki.write({"entity": entity, "expanded": expanded_entity, "url": url})
        return None


def load_publico_texts():
    # ToDo: allow to get publico articles text for disambiguation
    with open('publico_to_be_processed.txt') as f_in:
        for line in f_in:
            date, url, title = line.split('\t')


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
