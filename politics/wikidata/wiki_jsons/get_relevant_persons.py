import sys

import requests
from SPARQLWrapper import SPARQLWrapper, JSON

from politics.utils import just_sleep

endpoint_url = "https://query.wikidata.org/sparql"

query = """SELECT DISTINCT ?person ?personLabel
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
        UNION
          { VALUES ?positions { wd:Q19953703 wd:Q1723031 wd:Q322459 wd:Q1101237 
                                  wd:Q43185970 wd:Q82560916 }
            ?person p:P39 ?position_held.
            ?position_held ps:P39 ?positions .
            ?person rdfs:label ?personLabel
          }

        FILTER(LANG(?personLabel) = "pt")

    } ORDER BY ?personLabel"""


def get_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def main():

    base_url = "https://www.wikidata.org/wiki/Special:EntityData?"
    results = get_results(endpoint_url, query)
    wiki_ids = [r['person']['value'].split("/")[-1] for r in results["results"]["bindings"]]
    wiki_json = [base_url+wiki_id+'.json' for wiki_id in wiki_ids]
    for wiki_id, url in zip(wiki_ids, wiki_json):
        print(url)
        just_sleep(2)
        r = requests.get(url, params={'format': 'json', 'id': wiki_id})
        open(wiki_id+'.json', 'wt').write(r.text)


if __name__ == '__main__':
    main()
