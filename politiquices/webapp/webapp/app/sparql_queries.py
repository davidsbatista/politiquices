import sys

from SPARQLWrapper import SPARQLWrapper, JSON
from politiquices.webapp.webapp.app.data_models import OfficePosition, PoliticalParty, Person
from politiquices.webapp.webapp.app.utils import convert_dates

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


def get_nr_articles_per_year():
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


def get_total_nr_of_articles():
    query = """
        PREFIX        dc: <http://purl.org/dc/elements/1.1/>
        PREFIX my_prefix: <http://some.namespace/with/name#>

        SELECT (COUNT(?x) as ?nr_articles) WHERE {
            ?x my_prefix:arquivo ?y .
        }
        """
    results = query_sparql(prefixes + "\n" + query, "local")
    return results["results"]["bindings"][0]["nr_articles"]["value"]


def get_total_nr_articles_for_each_person():
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


def get_nr_of_persons():
    query = """
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        
        SELECT (COUNT(?x) as ?nr_persons) WHERE {
            ?x wdt:P31 wd:Q5
            } 
        """
    results = query_sparql(prefixes + "\n" + query, "local")
    return results["results"]["bindings"][0]["nr_persons"]["value"]


def get_person_info(wiki_id):
    query = f"""SELECT DISTINCT ?name ?image_url ?political_partyLabel ?political_party_logo 
                                ?officeLabel ?start ?end
                WHERE {{
                    wd:{wiki_id} rdfs:label ?name filter (lang(?name) = "pt").
                    OPTIONAL {{ wd:{wiki_id} wdt:P18 ?image_url. }}
                    OPTIONAL {{ 
                        wd:{wiki_id} p:P102 ?political_partyStmnt. 
                        ?political_partyStmnt ps:P102 ?political_party. 
                        OPTIONAL {{ ?political_party wdt:P154 ?political_party_logo. }}
                    }}
                    OPTIONAL {{
                        wd:{wiki_id} p:P39 ?officeStmnt.
                        ?officeStmnt ps:P39 ?office.
                        OPTIONAL {{ ?officeStmnt pq:P580 ?start. }}
                        OPTIONAL {{ ?officeStmnt pq:P582 ?end. }}
                    }}
                    SERVICE wikibase:label {{
                        bd:serviceParam wikibase:language "pt". 
                    }}
                }}
            """
    results = query_sparql(query, "wiki")
    name = None
    image_url = None
    parties = []
    offices = []
    for e in results["results"]["bindings"]:
        if not name:
            name = e["name"]['value']

        if not image_url:
            if 'image_url' in e:
                image_url = e["image_url"]["value"]

        # political parties
        party = PoliticalParty(
            name=e["political_partyLabel"]['value'] if 'political_partyLabel' in e else None,
            image_url=e["political_party_logo"]['value'] if 'political_party_logo' in e else None
        )
        if party not in parties:
            parties.append(party)

        # office positions
        if 'officeLabel' in e:
            office_position = OfficePosition(
                start=convert_dates(e["start"]["value"]) if 'start' in e else None,
                end=convert_dates(e["end"]["value"]) if 'end' in e else None,
                position=e["officeLabel"]["value"],
            )
            if office_position not in offices:
                offices.append(office_position)
    person = Person(wiki_id=wiki_id,
                    name=name,
                    image_url=image_url,
                    parties=parties,
                    positions=offices)
    return person


def get_person_relationships(wiki_id, rel_type, reverse=False):
    """
    :param reverse:
    :param wiki_id:
    :param rel_type: ent1_opposes_ent2, ent1_support_ent2,
    :return:
    """

    # set the order of the relationship, by default wiki_id is ent1
    arg_order = f"""
                ?rel my_prefix:ent1 wd:{wiki_id} .
                ?rel my_prefix:ent2 ?other_ent .
                """

    # otherwise swap arguments
    if reverse:
        arg_order = f"""
                    ?rel my_prefix:ent2 wd:{wiki_id} .
                    ?rel my_prefix:ent1 ?other_ent .
                    """

    query = f"""
        SELECT DISTINCT ?arquivo_doc ?date ?title ?other_ent ?other_ent_name
        WHERE {{
          {arg_order}
          ?rel my_prefix:type ?rel_type .
          ?other_ent rdfs:label ?other_ent_name .
          ?rel my_prefix:arquivo ?arquivo_doc .
          ?arquivo_doc dc:title ?title .
          ?arquivo_doc dc:date  ?date .
          FILTER (?rel_type = "{rel_type}")
        }}
        ORDER BY ?date
        """

    results = query_sparql(prefixes + "\n" + query, "local")
    relations = []

    for e in results["results"]["bindings"]:
        rel = {
            "url": e["arquivo_doc"]["value"],
            "title": e["title"]["value"],
            "date": e["date"]["value"].split("T")[0],
            "other_ent_url": 'entity?q='+e["other_ent"]["value"].split("/")[-1],
            "other_ent_name": e["other_ent_name"]["value"],
        }
        relations.append(rel)

    return relations


def get_person_relationships_by_month_year(wiki_id, rel_type, reverse=False):

    # set the order of the relationship, by default wiki_id is ent1
    arg_order = f"""
                ?rel my_prefix:ent1 wd:{wiki_id} .
                ?rel my_prefix:ent2 ?other_ent .
                """

    # otherwise swap arguments
    if reverse:
        arg_order = f"""
                    ?rel my_prefix:ent2 wd:{wiki_id} .
                    ?rel my_prefix:ent1 ?other_ent .
                    """

    query = f"""
        SELECT ?year ?month (COUNT(?arquivo_doc) as ?nr_articles)
        WHERE {{
          {arg_order}
          ?rel my_prefix:type ?rel_type .
          ?other_ent rdfs:label ?other_ent_name .
          ?rel my_prefix:arquivo ?arquivo_doc .
          ?arquivo_doc dc:title ?title .
          ?arquivo_doc dc:date  ?date .
          FILTER (?rel_type = "{rel_type}")
        }}
        GROUP BY (YEAR(?date) AS ?year) (MONTH(?date) AS ?month)
        ORDER BY ?year
        """
    result = query_sparql(prefixes + "\n" + query, "local")
    # dicts are insertion ordered
    year_month_articles = dict()
    for x in result["results"]["bindings"]:
        year = x["year"]["value"]
        month = x["month"]["value"]
        year_month_articles[(str(year)+'-'+str(month))] = int(x["nr_articles"]["value"])
    return year_month_articles


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


def query_sparql(query, endpoint):
    if endpoint == "wiki":
        endpoint_url = "https://query.wikidata.org/sparql"
    elif endpoint == "local":
        endpoint_url = "http://0.0.0.0:3030/arquivo/query"
    else:
        print("endpoint not valid")
        return None

    # ToDo: see user agent policy: https://w.wiki/CX6
    user_agent = "Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results
