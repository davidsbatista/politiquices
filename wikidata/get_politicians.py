import json
import sys
from SPARQLWrapper import SPARQLWrapper, JSON

endpoint_url = "https://query.wikidata.org/sparql"

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


def get_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


results = get_results(endpoint_url, query)

with open('politicians_no_parties.json', 'wt') as f_out:
    json.dump(results, f_out)
