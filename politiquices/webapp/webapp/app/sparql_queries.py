import sys

from SPARQLWrapper import SPARQLWrapper, JSON

prefixes = """
    PREFIX       wdt:  <http://www.wikidata.org/prop/direct/>
    PREFIX        wd:  <http://www.wikidata.org/entity/>
    PREFIX        bd:  <http://www.bigdata.com/rdf#>
    PREFIX  wikibase:  <http://wikiba.se/ontology#>
    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX		 ns2: <http://www.w3.org/2004/02/skos/core#>
    """


def initalize():
    query = """
        SELECT DISTINCT ?item ?label ?image_url{
            ?item wdt:P31 wd:Q5.
            SERVICE <https://query.wikidata.org/sparql> {
                ?item wdt:P31 wd:Q5.
                OPTIONAL { ?item wdt:P18 ?image_url. }
                SERVICE wikibase:label { 
                    bd:serviceParam wikibase:language "pt". 
                    ?item rdfs:label ?label }
                }
            }
        ORDER BY ?label
        """
    return prefixes+"\n"+query


def query_sparql(query, endpoint):
    if endpoint == "wiki":
        endpoint_url = "https://query.wikidata.org/sparql"
    elif endpoint == "local":
        endpoint_url = "http://localhost:3030/arquivo/query"
    else:
        print("endpoint not valid")
        return None

    # TODO adjust user agent; see https://w.wiki/CX6
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results
