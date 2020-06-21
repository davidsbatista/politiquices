import sys

from SPARQLWrapper import SPARQLWrapper, JSON
from functools import lru_cache

from politics.utils import just_sleep, read_ground_truth, write_iterator_to_file

ent_string = []
ent_true = []
ent_pred = []
ent_string_pred = []


def query_wikidata(entity_name):
    mappings = {
        'Costa': 'António Costa',
        'Durão': 'Durão Barroso',
        'Nobre': 'Fernando Nobre',
        'Marques Mendes': 'Luís Marques Mendes',
        'Marcelo': 'Marcelo Rebelo de Sousa',
        'Menezes': 'Luís Filipe Menezes',
        'Soares': 'Mário Soares'
    }

    entity_name = mappings.get(entity_name, entity_name)
    entity_name_parts = entity_name.split()
    entity_name_regex = '.*' + '.*'.join(entity_name_parts) + '.*'
    endpoint_url = "https://query.wikidata.org/sparql"

    query = f"""
    SELECT DISTINCT ?person ?personLabel
        WHERE {{
          {{ ?party wdt:P31 wd:Q7278 .
             ?party wdt:P17 wd:Q45 .
             ?person wdt:P102 ?party . 
             ?person rdfs:label ?personLabel }}
        UNION
          {{ VALUES ?positions {{ wd:Q19953703 wd:Q1723031 wd:Q322459 wd:Q1101237 
                                  wd:Q43185970 wd:Q82560916 }}
            ?person p:P39 ?position_held.
            ?position_held ps:P39 ?positions .
            ?person rdfs:label ?personLabel
          }}
        
        FILTER(LANG(?personLabel) = "pt")
        FILTER(regex(?personLabel, "{entity_name_regex}", "i"))

    }} ORDER BY ?personLabel
    """

    print("querying for entity: ", entity_name_regex)

    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    return sparql.query().convert()


@lru_cache(5000)
def query(entity):
    just_sleep()
    r = query_wikidata(entity)

    return r


def main():
    data = read_ground_truth()

    count = 0

    for x in data:

        if count % 5 == 0:
            print(query.cache_info())
            print(count)

        if 'wiki' in x['ent1_id']:
            entity_str = x['ent1']
            entity_id = x['ent1_id']
            ent_string.append(entity_str)
            ent_true.append(entity_id)
            r = query(entity_str)
            if len(r['results']['bindings']) == 0:
                ent_pred.append(None)
                ent_string_pred.append(None)

            elif len(r['results']['bindings']) == 1:
                ent_pred.append(r['results']['bindings'][0]['person']['value'])
                ent_string_pred.append(r['results']['bindings'][0]['personLabel']['value'])

            else:
                ent_pred.append(r['results']['bindings'][0]['person']['value'])
                ent_string_pred.append(r['results']['bindings'][0]['personLabel']['value'])
            count += 1

        if 'wiki' in x['ent2_id']:
            entity_str = x['ent2']
            entity_id = x['ent2_id']

            ent_string.append(entity_str)
            ent_true.append(entity_id)
            r = query(entity_str)
            if len(r['results']['bindings']) == 0:
                ent_pred.append(None)
                ent_string_pred.append(None)

            elif len(r['results']['bindings']) == 1:
                ent_pred.append(r['results']['bindings'][0]['person']['value'])
                ent_string_pred.append(r['results']['bindings'][0]['personLabel']['value'])

            else:
                ent_pred.append(r['results']['bindings'][0]['person']['value'])
                ent_string_pred.append(r['results']['bindings'][0]['personLabel']['value'])
            count += 1

    correct = []
    not_found = []
    wrong = []

    for true_string, true_id, pred_string, pred_id in zip(ent_string, ent_true, ent_string_pred, ent_pred):

        # entities that could not be found
        if pred_id is None:
            not_found.append((true_string, true_id))

        # correct
        elif true_id.split("/")[-1] == pred_id.split("/")[-1]:
            correct.append((true_string, true_id))

        # entities that are wrong
        elif true_id != pred_id:
            wrong.append((true_string, true_id, pred_string, pred_id))

        else:
            print("should never be reached")

    print("CORRECT  : ", len(correct))
    print("NOT FOUND: ", len(not_found))
    print("WRONG    : ", len(wrong))
    print()
    print("accuracy: ", float(len(correct)) / len(ent_string))

    write_iterator_to_file(correct, 'entity_linking_correct.txt')
    write_iterator_to_file(not_found, 'entity_linking_not_found.txt')
    write_iterator_to_file(wrong, 'entity_linking_wrong.txt')

    # accuracy:  0.7530647985989493
    # accuracy:  0.7968476357267951

    # CORRECT: 3194
    # NOT FOUND: 628
    # WRONG: 175
    # accuracy: 0.7990993244933701


if __name__ == '__main__':
    main()
