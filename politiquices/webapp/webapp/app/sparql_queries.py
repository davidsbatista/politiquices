import sys
from typing import Tuple, List, Dict

from cachew import cachew as cache_fixe
from SPARQLWrapper import SPARQLWrapper, JSON
from politiquices.webapp.webapp.app.data_models import (
    OfficePosition,
    PoliticalParty,
    Person,
    Relationship,
    RelationshipType,
)
from politiquices.webapp.webapp.app.utils import convert_dates

socrates = None
no_image = "/static/images/no_picture.jpg"
ps_logo = "/static/images/Logo_do_Partido_Socialista(Portugal).png"

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


def get_nr_articles_per_year() -> Tuple[List[int], List[int]]:
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


def get_total_nr_of_articles() -> int:
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
        ORDER BY DESC (?count)
        """
    return prefixes + "\n" + query


def get_nr_of_persons() -> int:
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
    query = f"""SELECT DISTINCT ?name ?image_url ?political_party ?political_partyLabel 
                                ?political_party_logo ?officeLabel ?start ?end
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
            name = e["name"]["value"]

        if not image_url:
            image_url = e["image_url"]["value"] if "image_url" in e else no_image

        # political parties
        if "political_party" in e:
            party_image_url = no_image
            # add 'PS' logo since it's on on wikidata
            if e["political_party"]["value"] == "http://www.wikidata.org/entity/Q847263":
                party_image_url = ps_logo

            party = PoliticalParty(
                wiki_id=e["political_party"]["value"].split("/")[-1],
                name=e["political_partyLabel"]["value"] if "political_partyLabel" in e else None,
                image_url=e["political_party_logo"]["value"]
                if "political_party_logo" in e
                else party_image_url,
            )
            if party not in parties:
                parties.append(party)

        # office positions
        if "officeLabel" in e:
            office_position = OfficePosition(
                start=convert_dates(e["start"]["value"]) if "start" in e else None,
                end=convert_dates(e["end"]["value"]) if "end" in e else None,
                position=e["officeLabel"]["value"],
            )
            if office_position not in offices:
                offices.append(office_position)

    return Person(
        wiki_id=wiki_id, name=name, image_url=image_url, parties=parties, positions=offices
    )


def get_person_relationships(wiki_id: str, rel_type: str, reverse: bool = False) -> List[Dict]:
    """
    :param reverse:
    :param wiki_id:
    :param rel_type: ent1_opposes_ent2, ent1_support_ent2,
    :return:
    """

    # set the order of the relationship, by default wiki_id is ent1
    arg_order = f"""
                ?rel my_prefix:ent1 wd:{wiki_id} .
                ?rel my_prefix:ent1_str ?focus_ent .
                ?rel my_prefix:ent2 ?other_ent .
                ?rel my_prefix:ent2_str ?other_ent_name .
                """

    # otherwise swap arguments
    if reverse:
        arg_order = f"""
                    ?rel my_prefix:ent2 wd:{wiki_id} .
                    ?rel my_prefix:ent2_str ?focus_ent .
                    ?rel my_prefix:ent1 ?other_ent .
                    ?rel my_prefix:ent1_str ?other_ent_name .
                    """

    query = f"""
        SELECT DISTINCT ?arquivo_doc ?date ?title ?score ?focus_ent ?other_ent ?other_ent_name
        WHERE {{
          {arg_order}
          
          ?rel my_prefix:type ?rel_type;
               my_prefix:score ?score.
          ?rel my_prefix:arquivo ?arquivo_doc .
          
          ?arquivo_doc dc:title ?title .
          ?arquivo_doc dc:date  ?date .
          
          FILTER (?rel_type = "{rel_type}")
        }}
        ORDER BY ASC(?score)
        """

    results = query_sparql(prefixes + "\n" + query, "local")
    relations = []

    for e in results["results"]["bindings"]:
        rel = {
            "url": e["arquivo_doc"]["value"],
            "title": e["title"]["value"],
            "score": str(e["score"]["value"])[0:5],
            "date": e["date"]["value"].split("T")[0],
            "focus_ent": e["focus_ent"]["value"],
            "other_ent_url": "entity?q=" + e["other_ent"]["value"].split("/")[-1],
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
        year_month_articles[(str(year) + "-" + str(month))] = int(x["nr_articles"]["value"])
    return year_month_articles


def get_list_of_persons_from_some_party_opposing_someone(wiki_id="Q182367", party="Q847263"):

    global socrates

    if socrates:
        return socrates

    query = f"""        
        SELECT DISTINCT ?ent1 ?ent1_name ?image_url ?arquivo_doc ?date ?title ?score
        WHERE {{
            ?rel my_prefix:type "ent1_opposes_ent2";
                 my_prefix:ent2 wd:{wiki_id};
                 my_prefix:ent1 ?ent1;
                 my_prefix:score ?score;
                 my_prefix:arquivo ?arquivo_doc .
            ?arquivo_doc dc:title ?title;
                         dc:date ?date.
            ?ent1 rdfs:label ?ent1_name .
            
            SERVICE <https://query.wikidata.org/sparql> {{
                ?ent1 wdt:P102 wd:{party};
                      rdfs:label ?personLabel.
                FILTER(LANG(?personLabel) = "pt")
                OPTIONAL {{ ?ent1 wdt:P18 ?image_url. }}
                SERVICE wikibase:label {{ 
                    bd:serviceParam wikibase:language "pt". ?item rdfs:label ?label 
                }}
            }}
        }}
        ORDER BY DESC(?date) ASC(?score)
        """
    result = query_sparql(prefixes + "\n" + query, "local")
    results = []
    for x in result["results"]["bindings"]:
        image = x["image_url"]["value"] if "image_url" in x else no_image
        person = Person(name=x["ent1_name"]["value"], wiki_id=x["ent1"]["value"], image_url=image)
        rel = Relationship(
            article_title=x["title"]["value"],
            article_url=x["arquivo_doc"]["value"],
            article_date=x["date"]["value"].split("T")[0],
            rel_type=RelationshipType.ent1_opposes_ent2,
            rel_score=x["score"]["value"][0:5],
            ent1=person,
            ent2=Person(wiki_id=wiki_id),
        )
        results.append(rel)

    socrates = results

    return results


def get_persons_affiliated_with_party(political_party: str) -> List[Person]:

    query = f"""
        SELECT DISTINCT ?person ?personLabel ?image_url {{
          ?person wdt:P31 wd:Q5.
          SERVICE <https://query.wikidata.org/sparql> {{
              ?person wdt:P102 wd:{political_party} .
              ?person rdfs:label ?personLabel .
              OPTIONAL {{ ?person wdt:P18 ?image_url. }}
              FILTER(LANG(?personLabel) = "pt")
          }}
        }}
        """

    results = query_sparql(prefixes + "\n" + query, "local")
    persons = []
    for x in results["results"]["bindings"]:
        image = x["image_url"]["value"] if "image_url" in x else no_image
        persons.append(
            Person(name=x["personLabel"]["value"],
                   wiki_id=x["person"]["value"].split("/")[-1],
                   image_url=image)
        )
    return persons


def get_top_relationships(wiki_id: str):
    query = f"""
        SELECT ?rel_type ?ent2 ?ent2_name (COUNT(?arquivo_doc) as ?nr_articles)
        WHERE {{ 
          ?rel my_prefix:ent1 wd:{wiki_id}  .
          ?rel my_prefix:ent2 ?ent2 .
          ?ent2 rdfs:label ?ent2_name .
          ?rel my_prefix:type ?rel_type .
          ?rel my_prefix:arquivo ?arquivo_doc .
          FILTER(?rel_type != "other")
        }} GROUP BY ?rel_type ?ent2 ?ent2_name
        ORDER BY ?rel_type DESC(?nr_articles)
        """
    results = query_sparql(prefixes + "\n" + query, "local")
    persons = []
    for x in results["results"]["bindings"]:
        persons.append(
            {'wiki_id': x['ent2']['value'].split("/")[-1],
             'name': x['ent2_name']['value'],
             'rel_type': x['rel_type']['value'],
             'nr_articles': int(x['nr_articles']['value']),
             }
        )
    return persons


def get_all_parties():
    query = """
        SELECT DISTINCT ?political_party ?party_label ?party_logo (COUNT(?person) as ?nr_personalities){
            ?person wdt:P31 wd:Q5 .
            SERVICE <https://query.wikidata.org/sparql> {
                ?person wdt:P102 ?political_party .
                ?political_party rdfs:label ?party_label .
                OPTIONAL {?political_party wdt:P154 ?party_logo. } 
                FILTER(LANG(?party_label) = "pt")
          }
        } GROUP BY ?political_party ?party_label ?party_logo
        ORDER BY DESC(?nr_personalities)
        """
    results = query_sparql(prefixes + "\n" + query, "local")
    political_parties = []
    for x in results["results"]["bindings"]:
        if 'party_logo' in x:
            party_logo = x['party_logo']['value']
        else:
            if x['political_party']['value'].split("/")[-1] == 'Q847263':
                party_logo = ps_logo
            else:
                party_logo = no_image
        political_parties.append(
            {'wiki_id': x['political_party']['value'].split("/")[-1],
             'party_label': x['party_label']['value'],
             'party_logo': party_logo,
             'nr_personalities': x['nr_personalities']['value'],
             }
        )

    return political_parties


def initalize():
    # get: wiki_id, name(label), image_url
    query = """
        SELECT DISTINCT ?item ?label ?image_url {
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
