import json
import sys

import requests
from SPARQLWrapper import SPARQLWrapper, JSON

from politiquices.extraction.utils import just_sleep

# PERSONS

# persons that are/were affiliated with a recent/relevant portuguese political party
affiliated_with_relevant_political_party = """
    SELECT DISTINCT ?person ?personLabel
        WHERE {
          { VALUES ?relevant_parties 
                { wd:Q59325416 wd:Q884840 wd:Q1054298 wd:Q63645885 wd:Q46122950 wd:Q19694667 
                   wd:Q16947563 wd:Q6516904 wd:Q5899673 wd:Q605026 wd:Q20895387 wd:Q5154439 
                   wd:Q2054628 wd:Q10345627 wd:Q1819658 wd:Q6540639 wd:Q2054681 wd:Q1332539 
                   wd:Q1851550 wd:Q595575 wd:Q847263 wd:Q2054807 wd:Q3293542 wd:Q7232654 
                   wd:Q20901233 wd:Q10345705 wd:Q2054840 wd:Q1352945 wd:Q2105350 wd:Q18166125 
                   wd:Q65164025 wd:Q769829
                }
             ?person wdt:P102 ?relevant_parties . 
             ?person rdfs:label ?personLabel }
        FILTER(LANG(?personLabel) = "pt")
    } ORDER BY ?personLabel
    """

# portuguese persons based on their occupation(s) AND born after 1935
# wd:Q1930187  jornalista
# wd:Q16533    juiz,
# wd:Q188094   economista
# wd:Q40348    advogado
# wd:Q212238   civil servant
# wd:Q82955    politician
# wd:Q43845    businessperson
# wd:Q131524   entrepreneur

portuguese_persons_occupations = """
    SELECT DISTINCT ?person ?personLabel ?date_of_birth
    WHERE {
      ?person wdt:P27 wd:Q45.
      { VALUES ?ocupations { wd:Q1930187 wd:Q16533 wd:Q188094 wd:Q40348 
                             wd:Q212238  wd:Q82955 wd:Q43845 wd:Q806798}} .
      ?person wdt:P106 ?ocupations .
      ?person wdt:P569 ?date_of_birth .
      ?person rdfs:label ?personLabel.
      FILTER(?date_of_birth >= "1935-01-01T00:00:00"^^xsd:dateTime )
      FILTER(LANG(?personLabel) = "pt")
    } 
    ORDER BY ?personLabel
    """

# ORGANISATIONS

# all portuguese political parties
portuguese_political_parties = """
    SELECT DISTINCT ?party ?partyLabel ?logo ?inception ?disbanded
    WHERE {
      ?party wdt:P31 wd:Q7278;
             wdt:P17 wd:Q45.
      OPTIONAL {
        ?party wdt:P154 ?logo.
      }
      OPTIONAL {
        ?party wdt:P576 ?disbanded.
        ?party wdt:P571 ?inception.
      }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "pt". }
    } ORDER BY ?partyLabel
    """

# portuguese banks or banks with headquarters in Lisbon
portuguese_banks = """
    SELECT DISTINCT ?bank ?bankLabel WHERE {
      { 
        VALUES ?bank_related_instances {wd:Q837171 wd:Q806718}
        ?bank wdt:P452 ?bank_related_instances;
          rdfs:label ?bankLabel.
        ?bank wdt:P17 wd:Q45.
      }
      UNION {
         ?bank wdt:P452 wd:Q806718;
          rdfs:label ?bankLabel.
        ?bank wdt:P159 wd:Q597
      }
      UNION {
         ?bank wdt:P31 wd:Q848507;
          rdfs:label ?bankLabel.
        ?bank wdt:P159 wd:Q597
      }

      FILTER((LANG(?bankLabel)) = "pt")
    }
    ORDER BY (?bankLabel)

    """

# all_portuguese_municipalities
portuguese_municipalities = """
    SELECT DISTINCT ?locality ?localityLabel WHERE {
        ?locality wdt:P31 wd:Q13217644;
           rdfs:label ?localityLabel.
      FILTER((LANG(?localityLabel)) = "pt")
    }
    ORDER BY (?localityLabel)
    """

# all public portuguese enterprises
portuguese_public_enterprises = """
    SELECT DISTINCT ?enterprise ?enterpriseLabel ?x WHERE {
        ?enterprise wdt:P31 wd:Q270791;
          rdfs:label ?enterpriseLabel.
        ?enterprise wdt:P17 wd:Q45;
      FILTER((LANG(?enterpriseLabel)) = "pt")
    }
    ORDER BY (?enterpriseLabel)
    """

# get a list of all possible public office positions hold by a someone portuguese
public_office_positions = """
    SELECT DISTINCT ?personLabel ?person ?positionLabel ?position WHERE {
        ?person wdt:P27 wd:Q45 .
        ?person rdfs:label ?personLabel .
        ?person wdt:P39 ?position.
        ?position rdfs:label ?positionLabel.
      FILTER((LANG(?personLabel)) = "pt")
      FILTER((LANG(?positionLabel)) = "pt")
    }
    ORDER BY (?personLabel)
    LIMIT 100
    """


def get_relevant_persons_based_on_public_office_positions():
    """
    Read the all the wikidata portuguese public offices objects from: `public_office_positions.json`
    and extract all the persons connected to it through the following property:

        wdt:P39 position held
        subject currently or formerly holds the object position or public office

        filter to return only those born after 1935

    :return:
    """

    wiki_ids = []
    with open("public_office_positions.json") as f_in:
        data = json.load(f_in)
        for k, v in data.items():
            for wiki_id, description in v.items():
                wiki_ids.append("wd:" + wiki_id)

    query = f"""
    SELECT DISTINCT ?person ?personLabel
    WHERE {{
      VALUES ?positions {{ {' '.join(wiki_ids)} }}
      ?person wdt:P39 ?positions.
      ?person rdfs:label ?personLabel .
      ?person wdt:P569 ?date_of_birth .
      FILTER(LANG(?personLabel) = "pt")
      FILTER(?date_of_birth >= "1935-01-01T00:00:00"^^xsd:dateTime )
    }} ORDER BY ?personLabel
    """

    return query


def get_results(endpoint_url, sarpql_query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(sarpql_query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def load_from_list(fname):
    with open(fname, 'rt') as f_in:
        wiki_ids_urls = [line.split(',')[0].split("/")[-1] for line in f_in]
    return wiki_ids_urls


def main():
    queries = [
        affiliated_with_relevant_political_party,
        get_relevant_persons_based_on_public_office_positions(),
        portuguese_persons_occupations,
    ]

    to_load = load_from_list('entities_to_add.txt')
    to_remove = load_from_list('entities_to_remove.txt')

    base_url = "https://www.wikidata.org/wiki/Special:EntityData?"
    endpoint_url = "https://query.wikidata.org/sparql"
    relevant_persons_ids = []
    default_dir = "wiki_jsons/"

    # get the wiki ids for all relevant persons
    for query in queries:
        results = get_results(endpoint_url, query)
        wiki_ids = [r["person"]["value"].split("/")[-1] for r in results["results"]["bindings"]]
        relevant_persons_ids.extend(wiki_ids)

    print(f'{len(relevant_persons_ids)} entities gathered from SPARQL queries')
    print(f'{len(to_load)} manually selected entities to be added')
    print(f'{len(to_remove)} manually selected entities to be removed')
    relevant_persons_ids.extend(to_load)
    for el in to_remove:
        if el in relevant_persons_ids:
            relevant_persons_ids.remove(el)
            print("Removed ", el)

    print(f'{len(relevant_persons_ids)} entities to be loaded')

    # get detailed information for each person
    for idx, wiki_id in enumerate(set(relevant_persons_ids)):
        print(str(idx) + "/" + str(len(set(relevant_persons_ids))))
        just_sleep(5)
        url = base_url + wiki_id + ".json"
        r = requests.get(url, params={"format": "json", "id": wiki_id})
        open(default_dir + wiki_id + ".json", "wt").write(r.text)


if __name__ == "__main__":
    main()
