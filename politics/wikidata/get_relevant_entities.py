import json
import sys

from SPARQLWrapper import SPARQLWrapper, JSON

from politics.utils import just_sleep, write_iterator_to_file, read_ground_truth

endpoint_url = "https://query.wikidata.org/sparql"


def get_portuguese_political_parties():
    query = """
    SELECT DISTINCT ?party ?partyLabel ?inception ?disbanded
    WHERE {
      ?party wdt:P31 wd:Q7278.
      ?party wdt:P17 wd:Q45.
      OPTIONAL {
        ?party wdt:P576 ?disbanded.
        ?party wdt:P571 ?inception
      }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "pt". }
    } ORDER BY ?partyLabel
    """

    return query


def get_people_that_are_members_of_a_portuguese_political_parties():
    query = """"
    SELECT DISTINCT ?person ?personLabel
    WHERE {
      ?party wdt:P31 wd:Q7278 .
      ?party wdt:P17 wd:Q45 .
      ?person wdt:P102 ?party .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "pt". }
    } ORDER BY ?personLabel
    """

    return query


def get_relevant_persons_based_on_positions():
    """
    Q19953703  member of the Portuguese parliament
    Q1723031   prime Minister of Portugal
    Q7614320   minister of economy
    Q4294919   Ministro dos Negócios Estrangeiros
    Q43186728  Ministro da Administração Interna
    Q25906445  Minister of National Defence
    Q25448371  President of the Assembly of the Republic

    Q322459    president of Portugal
    Q1101237   president of the Regional Government of Madeira
    Q43185970  mayor of Lisbon

    Q82560916  president of the Social Democratic Party
    """

    query = """
    SELECT DISTINCT ?person ?personLabel
    WHERE {
      VALUES ?positions { wd:Q19953703 wd:Q1723031 wd:Q322459 wd:Q1101237 wd:Q43185970 wd:Q82560916}
      ?person p:P39 ?position_held.
      ?position_held ps:P39 ?positions .
      ?person rdfs:label ?personLabel
      FILTER(LANG(?personLabel) = "pt")
    } ORDER BY ?personLabel
    """

    return query


def get_relevant_persons_based_on_occupation():
    """
    wd:Q806798  bankers
    ('http://www.wikidata.org/entity/Q484876', 'diretor executivo')
    ('http://www.wikidata.org/entity/Q16533', 'juiz')
    ('http://www.wikidata.org/entity/Q82955', 'político')


    :return:
    """
    query = """
    SELECT DISTINCT ?person ?personLabel
    WHERE {
        VALUES ?occupations { wd:Q806798}
        ?person p:P106 ?occupation.
        ?occupation ps:P106 ?occupations .
        ?person wdt:P27 wd:Q45.
        ?person rdfs:label ?personLabel
        FILTER(LANG(?personLabel) = "pt")
      }
    ORDER BY ?personLabel
    """

    return query


def get_relevant_political_persons():

    # everyone belonging to a portuguese political party or which had any
    # of the positions like above

    query = """
    SELECT DISTINCT ?person ?personLabel
    WHERE {
        { ?party wdt:P31 wd:Q7278 .
          ?party wdt:P17 wd:Q45 .
          ?person wdt:P102 ?party .
          ?person rdfs:label ?personLabel
        }
    UNION
        { VALUES ?positions { wd:Q19953703 wd:Q1723031 wd:Q322459 wd:Q82560916}
          ?person p:P39 ?position_held.
          ?position_held ps:P39 ?positions .
          ?person rdfs:label ?personLabel
        }
        FILTER(LANG(?personLabel) = "pt")
    } ORDER BY ?personLabel


    :return:
    """

    return query


def get_results(query):
    # TODO adjust user agent; see https://w.wiki/CX6
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    just_sleep()
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def query_member_political_party():
    query = """SELECT DISTINCT ?person ?personLabel
        WHERE
        {
          ?person wdt:P27 wd:Q45.
          ?person wdt:P102 ?portuguese_party.
          ?person rdfs:label ?personLabel.
          {SELECT DISTINCT ?portuguese_party
           WHERE
                {
                  ?subj wdt:P31 wd:Q7278.
                  ?subj wdt:P17 wd:Q45.
                  ?subj rdfs:label ?portuguese_partyLabel.
                  #FILTER(LANG(?portuguese_partyLabel) = "pt")
                  #SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],pt". }
                }
           }
          FILTER(LANG(?personLabel) = "pt")
          SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],pt". }
        }
    ORDER BY ?personLabel
    """

    results = get_results(query)
    with open('politicians_no_parties.json', 'wt') as f_out:
        json.dump(results, f_out)


def get_properties_of_annotated_entity(wiki_id):
    # instance of: https://www.wikidata.org/wiki/Property:P31
    # occupation: https://www.wikidata.org/wiki/Property:P106
    # position_held: https://www.wikidata.org/wiki/Property:P39

    query = f"""SELECT DISTINCT ?instance_of ?occupation ?position ?occupation_label ?position_label ?instance_of_label
    WHERE
      {{
        wd:{wiki_id} p:P31 ?instance_of_stmt .
        ?instance_of_stmt ps:P31 ?instance_of .

        OPTIONAL {{
              wd:{wiki_id} p:P106 ?occupation_of_stmt .
              ?occupation_of_stmt ps:P106 ?occupation .
              ?occupation rdfs:label ?occupation_label .

              wd:{wiki_id} p:P39 ?positions_stmt .
              ?positions_stmt ps:P39 ?position .
              ?position rdfs:label ?position_label .
        }}
        FILTER(LANG(?occupation_label) = "pt")
        FILTER(LANG(?position_label) = "pt")
      }}"""

    return get_results(query)


def main():
    data = read_ground_truth()
    ids = set()
    for d in data:
        ids.add(d['ent1_id']) if 'wikidata' in d['ent1_id'] else None
        ids.add(d['ent2_id']) if 'wikidata' in d['ent2_id'] else None

    for i in ids:
        print(i)

    occupation = set()
    position = set()
    instance_of = set()

    count = 0

    for wiki_url in sorted(ids):
        if count % 10 == 0:
            print(count)
        wiki_id = wiki_url.split("/")[-1]
        results = get_properties_of_annotated_entity(wiki_id)
        for r in results['results']['bindings']:
            occupation.add((r['occupation']['value'], r['occupation_label']['value']))
            position.add((r['position']['value'], r['position_label']['value']))
            instance_of.add(r['instance_of']['value'])
        count += 1

    write_iterator_to_file(occupation, 'occupations.txt')
    write_iterator_to_file(position, 'positions.txt')
    write_iterator_to_file(instance_of, 'instances_of.txt')


if __name__ == '__main__':
    main()
