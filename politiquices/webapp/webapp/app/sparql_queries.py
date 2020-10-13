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


def nr_articles_per_year():
    query = """
        PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    
        SELECT ?year (COUNT(?x) as ?nr_articles) WHERE {
          ?x dc:date ?date .
        }
        GROUP BY (YEAR(?date) AS ?year)
        ORDER BY ?year
        """
    result = query_sparql(prefixes + "\n" + query, "local")
    year = []
    nr_articles = []

    for x in result["results"]["bindings"]:
        year.append(int(x["year"]["value"]))
        nr_articles.append(int(x["nr_articles"]["value"]))
    return year, nr_articles


def nr_of_persons():
    query = """
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    
        SELECT (COUNT(?x) as ?nr_persons) WHERE {
            ?x wdt:P31 wd:Q5
            } 
        """
    results = query_sparql(prefixes + "\n" + query, "local")
    return results["results"]["bindings"][0]["nr_persons"]["value"]


def total_nr_of_articles():
    query = """
        PREFIX        dc: <http://purl.org/dc/elements/1.1/>
        PREFIX my_prefix: <http://some.namespace/with/name#>
    
        SELECT (COUNT(?x) as ?nr_articles) WHERE {
            ?x my_prefix:arquivo ?y .
        }
        """
    results = query_sparql(prefixes + "\n" + query, "local")
    return results["results"]["bindings"][0]["nr_articles"]["value"]


def initalize():
    # get: wiki_id, name(label), image_url
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
    return prefixes + "\n" + query


def counts():
    query = """
        SELECT ?person_name ?person (COUNT(*) as ?count){
            ?person rdfs:label ?person_name .
            ?person wdt:P31 wd:Q5 .
            {?rel my_prefix:ent1 ?person} UNION {?rel my_prefix:ent2 ?person} .
            ?rel my_prefix:arquivo ?arquivo_doc .
            ?arquivo_doc dc:title ?title .
            }
        GROUP BY ?person_name ?person
        HAVING (count(distinct *) > 1)
        ORDER BY DESC (?count)
        """
    return prefixes + "\n" + query


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
