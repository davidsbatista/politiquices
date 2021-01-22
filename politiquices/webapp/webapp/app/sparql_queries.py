import sys
from typing import Tuple, List
from collections import defaultdict

from functools import lru_cache
from SPARQLWrapper import SPARQLWrapper, JSON
from politiquices.webapp.webapp.app.data_models import OfficePosition, Person, PoliticalParty

wikidata_endpoint = "http://0.0.0.0:3030/wikidata/query"
live_wikidata = "https://query.wikidata.org/sparql"

no_image = "/static/images/no_picture.jpg"
ps_logo = "/static/images/Logo_do_Partido_Socialista(Portugal).png"

politiquices_prefixes = """    
    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX		 ns2: <http://www.w3.org/2004/02/skos/core#>
    """

wikidata_prefixes = """
    PREFIX        wd: <http://www.wikidata.org/entity/>
    PREFIX       wds: <http://www.wikidata.org/entity/statement/>
    PREFIX       wdv: <http://www.wikidata.org/value/>
    PREFIX       wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX  wikibase: <http://wikiba.se/ontology#>
    PREFIX         p: <http://www.wikidata.org/prop/>
    PREFIX        ps: <http://www.wikidata.org/prop/statement/>
    PREFIX        pq: <http://www.wikidata.org/prop/qualifier/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX        bd: <http://www.bigdata.com/rdf#>
    """

prefixes = politiquices_prefixes + wikidata_prefixes


# Status/Statistics #
@lru_cache
def get_nr_articles_per_year() -> Tuple[List[int], List[int]]:
    query = """
        PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    
        SELECT ?year (COUNT(?x) as ?nr_articles) WHERE {
          ?x dc:date ?date .
        }
        GROUP BY (YEAR(?date) AS ?year)
        ORDER BY ?year
        """
    result = query_sparql(prefixes + "\n" + query, "politiquices")
    year = []
    nr_articles = []

    for x in result["results"]["bindings"]:
        year.append(int(x["year"]["value"]))
        nr_articles.append(int(x["nr_articles"]["value"]))

    return year, nr_articles


@lru_cache
def get_total_nr_of_articles() -> int:
    query = """
        PREFIX        dc: <http://purl.org/dc/elements/1.1/>
        PREFIX my_prefix: <http://some.namespace/with/name#>

        SELECT (COUNT(?x) as ?nr_articles) WHERE {
            ?x my_prefix:arquivo ?y .
        }
        """
    results = query_sparql(prefixes + "\n" + query, "politiquices")
    return results["results"]["bindings"][0]["nr_articles"]["value"]


@lru_cache
def get_nr_of_persons() -> int:
    query = """
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        
        SELECT (COUNT(?x) as ?nr_persons) WHERE {
            ?x wdt:P31 wd:Q5
            } 
        """
    results = query_sparql(prefixes + "\n" + query, "politiquices")
    return results["results"]["bindings"][0]["nr_persons"]["value"]


# Run once on start-up #
@lru_cache()
def get_graph_links():
    query = """
        SELECT DISTINCT ?person_a ?rel_type ?person_b ?url {
        VALUES ?rel_values {'ent1_opposes_ent2' 'ent2_opposes_ent1' 
                            'ent1_supports_ent2' 'ent2_supports_ent1'
                            'ent1_other_ent2' 'ent2_other_ent1'} .
        ?rel my_prefix:type ?rel_values .  
        ?rel my_prefix:ent1 ?person_a .
        ?rel my_prefix:ent2 ?person_b .        
        ?rel my_prefix:type ?rel_type .
        ?rel my_prefix:arquivo ?url .
        }
        """
    results = query_sparql(prefixes + "\n" + query, "politiquices")
    edges = [
        {
            "person_a": x["person_a"]["value"],
            "person_b": x["person_b"]["value"],
            "rel_type": x["rel_type"]["value"],
            "url": x["url"]["value"],
        }
        for x in results["results"]["bindings"]
    ]
    return edges


@lru_cache()
def top_co_occurrences():
    query = """
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX my_prefix: <http://some.namespace/with/name#>
        
        SELECT DISTINCT ?person_a ?person_b (COUNT (?url) as ?n_artigos) {
          VALUES ?rel_values {'ent1_opposes_ent2' 'ent2_opposes_ent1' 
                              'ent1_supports_ent2' 'ent2_supports_ent1'} .
              
          ?rel my_prefix:type ?rel_values .
          {
            ?rel my_prefix:ent1 ?person_a .
            ?rel my_prefix:ent2 ?person_b .
          }
          UNION {
            ?rel my_prefix:ent2 ?person_a .
            ?rel my_prefix:ent1 ?person_b .
          }
          ?rel my_prefix:arquivo ?url .
          ?rel my_prefix:type ?rel_type .
        }
        GROUP BY ?person_a ?person_b
        ORDER BY DESC(?n_artigos)
        """
    results = query_sparql(prefixes + "\n" + query, "politiquices")
    co_occurrences = []
    seen = set()
    for x in results["results"]["bindings"]:
        person_a = x["person_a"]["value"]
        person_b = x["person_b"]["value"]
        artigos = x["n_artigos"]["value"]
        if person_a + " " + person_b in seen:
            continue
        co_occurrences.append({"person_a": person_a, "person_b": person_b, "n_artigos": artigos})
        seen.add(person_a + " " + person_b)
        seen.add(person_b + " " + person_a)

    return co_occurrences


@lru_cache
def all_persons_freq():
    query = """
        SELECT DISTINCT ?person (COUNT (?url) as ?n_artigos) {  
        VALUES ?rel_values {'ent1_opposes_ent2' 'ent2_opposes_ent1' 
                            'ent1_supports_ent2' 'ent2_supports_ent1'} .
        ?rel my_prefix:type ?rel_values .          
        { ?rel my_prefix:ent1 ?person .} UNION { ?rel my_prefix:ent2 ?person . }              
        ?rel my_prefix:arquivo ?url .
        ?rel my_prefix:type ?rel_type .        
        }
        GROUP BY ?person
        HAVING (?n_artigos > 0)
        ORDER BY DESC(?n_artigos)        
        """
    results = query_sparql(prefixes + "\n" + query, "politiquices")
    top_freq = [
        {"person": x["person"]["value"], "freq": x["n_artigos"]["value"]}
        for x in results["results"]["bindings"]
    ]
    return top_freq


@lru_cache
def all_entities():
    query = f"""
        SELECT DISTINCT ?item ?label ?image_url {{
            ?item wdt:P31 wd:Q5.
            SERVICE <{wikidata_endpoint}> {{
                ?item rdfs:label ?label .
                FILTER(LANG(?label) = "pt")
                OPTIONAL {{ ?item wdt:P18 ?image_url. }}                
                }}
            }}
        ORDER BY ?label
        """

    return prefixes + "\n" + query


@lru_cache
def get_total_nr_articles_for_each_person():
    query = """
        SELECT ?person_name ?person (COUNT(*) as ?count){
          ?person wdt:P31 wd:Q5 ;
                  rdfs:label ?person_name .            
          {?rel my_prefix:ent1 ?person} UNION {?rel my_prefix:ent2 ?person} .
           ?rel my_prefix:type ?rel_type 
             FILTER(?rel_type!="other") .
          ?rel my_prefix:arquivo ?arquivo_doc .
          ?arquivo_doc dc:title ?title .
        }
        GROUP BY ?person_name ?person
        ORDER BY DESC (?count) ASC (?person_name)
        """
    return prefixes + "\n" + query


# Parties #
@lru_cache
def get_persons_affiliated_with_party(political_party: str):
    query = f"""
        SELECT DISTINCT ?partyLabel ?political_party_logo ?person ?personLabel ?image_url {{
          ?person wdt:P31 wd:Q5.
          SERVICE <{wikidata_endpoint}> {{
              wd:{political_party} rdfs:label ?partyLabel FILTER(LANG(?partyLabel) = "pt") .
              OPTIONAL {{ wd:{political_party} wdt:P154 ?political_party_logo. }}
              ?person wdt:P102 wd:{political_party} .
              ?person rdfs:label ?personLabel FILTER(LANG(?personLabel) = "pt") .
              OPTIONAL {{ ?person wdt:P18 ?image_url. }}

          }}
        }} 
        ORDER BY ?personLabel
        """

    results = query_sparql(prefixes + "\n" + query, "politiquices")
    persons = []
    party_name = None
    party_logo = None

    # add 'PS' logo since it's not on wikidata
    if political_party == "Q847263":
        party_logo = ps_logo

    seen = set()
    for x in results["results"]["bindings"]:
        wiki_id = x["personLabel"]["value"]
        if wiki_id in seen:
            continue

        if not party_name:
            party_name = x["partyLabel"]["value"]

        if not party_logo:
            if "political_party_logo" in x:
                party_logo = x["political_party_logo"]["value"]
            else:
                party_logo = no_image

        image = x["image_url"]["value"] if "image_url" in x else no_image
        persons.append(
            Person(name=wiki_id, wiki_id=x["person"]["value"].split("/")[-1], image_url=image,)
        )
        seen.add(wiki_id)

    return persons, party_name, party_logo


@lru_cache
def get_wiki_id_affiliated_with_party(political_party: str):
    query = f"""
        SELECT DISTINCT ?wiki_id {{
            ?wiki_id wdt:P102 wd:{political_party}; .  
        }}
    """
    results = query_sparql(prefixes + "\n" + query, "wikidata")
    return [x["wiki_id"]["value"].split("/")[-1] for x in results["results"]["bindings"]]


# Personality Information
# ToDo: merge get_person_info() and get_person_info2()
@lru_cache
def get_person_info(wiki_id):
    query = f"""
        SELECT ?name ?office ?office_label ?image_url ?political_party_logo 
                ?political_party ?political_party_label 
        WHERE {{
            wd:{wiki_id} rdfs:label ?name
            FILTER(LANG(?name)="pt") .
            OPTIONAL {{ wd:{wiki_id} wdt:P18 ?image_url. }}
            OPTIONAL {{
                wd:{wiki_id} p:P39 ?officeStmnt.
                ?officeStmnt ps:P39 ?office.
                ?office rdfs:label ?office_label 
                    FILTER(LANG(?office_label)="pt")
            }}
            OPTIONAL {{
                wd:{wiki_id} p:P102 ?political_partyStmnt.
                ?political_partyStmnt ps:P102 ?political_party.
                ?political_party rdfs:label ?political_party_label 
                    FILTER(LANG(?political_party_label)="pt").
                OPTIONAL {{ ?political_party wdt:P154 ?political_party_logo. }}
            }}
        }}
    """
    results = query_sparql(prefixes + "\n" + query, "wikidata")

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
                name=e["political_party_label"]["value"] if "political_party_label" in e else None,
                image_url=e["political_party_logo"]["value"]
                if "political_party_logo" in e
                else party_image_url,
            )
            if party not in parties:
                parties.append(party)

        # office positions
        if "office_label" in e:
            office_position = OfficePosition(position=e["office_label"]["value"])
            if office_position not in offices:
                offices.append(office_position)

    results = get_person_detailed_info(wiki_id)

    return Person(
        wiki_id=wiki_id,
        name=name,
        image_url=image_url,
        parties=parties,
        positions=results["position"],
        education=results["education"],
        occupations=results["occupation"],
    )


@lru_cache
def get_person_detailed_info(wiki_id):
    occupation_query = f"""
        SELECT DISTINCT ?occupation_label
        WHERE {{
          wd:{wiki_id} p:P106 ?occupationStmnt .
          ?occupationStmnt ps:P106 ?occupation .
          ?occupation rdfs:label ?occupation_label FILTER(LANG(?occupation_label) = "pt").
        }}
        """

    education_query = f"""
        SELECT DISTINCT ?educatedAt_label
        WHERE {{
            wd:{wiki_id} p:P69 ?educatedAtStmnt .
            ?educatedAtStmnt ps:P69 ?educatedAt .
            ?educatedAt rdfs:label ?educatedAt_label FILTER(LANG(?educatedAt_label) = "pt").
            }}
        """

    positions_query = f"""
        SELECT DISTINCT ?position_label
        WHERE {{
            wd:{wiki_id} p:P39 ?positionStmnt .
            ?positionStmnt ps:P39 ?position .
            ?position rdfs:label ?position_label FILTER(LANG(?position_label) = "pt").
        }}
        """

    results = query_sparql(prefixes + "\n" + occupation_query, "wikidata")
    occupations = [x["occupation_label"]["value"] for x in results["results"]["bindings"]]

    results = query_sparql(prefixes + "\n" + education_query, "wikidata")
    education = [x["educatedAt_label"]["value"] for x in results["results"]["bindings"]]

    results = query_sparql(prefixes + "\n" + positions_query, "wikidata")
    positions = [x["position_label"]["value"] for x in results["results"]["bindings"]]

    return {"education": education, "occupation": occupations, "position": positions}


@lru_cache
def get_party_of_entity(wiki_id):
    query = f"""
        SELECT DISTINCT ?party ?party_label {{
            wd:{wiki_id} wdt:P31 wd:Q5.
            SERVICE <{wikidata_endpoint}> {{ 
                wd:{wiki_id} p:P102 ?partyStmnt .
                ?partyStmnt ps:P102 ?party.
                ?party rdfs:label ?party_label FILTER(LANG(?party_label)="pt") .  
            }}  
        }}
        """

    result = query_sparql(prefixes + "\n" + query, "politiquices")
    parties = []
    for x in result["results"]["bindings"]:
        parties.append(
            {"wiki_id": x["party"]["value"].split("/")[-1], "name": x["party_label"]["value"]}
        )
    return parties


@lru_cache
def get_person_relationships(wiki_id):
    query = f"""
        SELECT DISTINCT ?arquivo_doc ?date ?title ?rel_type ?score ?ent1 ?ent1_str ?ent2 ?ent2_str
        WHERE {{
         {{ ?rel my_prefix:ent1 wd:{wiki_id} }} UNION {{?rel my_prefix:ent2 wd:{wiki_id} }}
        
            ?rel my_prefix:type ?rel_type;
                 my_prefix:score ?score.
    
             ?rel my_prefix:ent1 ?ent1 ;
                  my_prefix:ent2 ?ent2 ;
                  my_prefix:ent1_str ?ent1_str ;
                  my_prefix:ent2_str ?ent2_str ;
                  my_prefix:arquivo ?arquivo_doc .
         
              ?arquivo_doc dc:title ?title ;
                           dc:date  ?date .
            }}
            ORDER BY ASC(?date)
        """

    results = query_sparql(prefixes + "\n" + query, "politiquices")
    relations = defaultdict(list)

    # ToDo: refactor to a function
    for e in results["results"]["bindings"]:
        ent1_wiki = e["ent1"]["value"].split("/")[-1].strip()
        ent2_wiki = e["ent2"]["value"].split("/")[-1].strip()

        if e["rel_type"]["value"] == "ent1_supports_ent2":

            if wiki_id == ent1_wiki:
                rel_type = "supports"
                other_ent_url = ent2_wiki
                other_ent_name = e["ent2_str"]["value"].split("/")[-1]
                focus_ent = e["ent1_str"]["value"].split("/")[-1]

            elif wiki_id == ent2_wiki:
                rel_type = "supported_by"
                other_ent_url = ent1_wiki
                other_ent_name = e["ent1_str"]["value"].split("/")[-1]
                focus_ent = e["ent2_str"]["value"].split("/")[-1]

        elif e["rel_type"]["value"] == "ent1_opposes_ent2":

            if wiki_id == ent1_wiki:
                rel_type = "opposes"
                other_ent_url = ent2_wiki
                other_ent_name = e["ent2_str"]["value"].split("/")[-1]
                focus_ent = e["ent1_str"]["value"].split("/")[-1]

            elif wiki_id == ent2_wiki:
                rel_type = "opposed_by"
                other_ent_url = ent1_wiki
                other_ent_name = e["ent1_str"]["value"].split("/")[-1]
                focus_ent = e["ent2_str"]["value"].split("/")[-1]

        elif e["rel_type"]["value"] == "ent2_supports_ent1":

            if wiki_id == ent2_wiki:
                rel_type = "supports"
                other_ent_url = ent1_wiki
                other_ent_name = e["ent1_str"]["value"].split("/")[-1]
                focus_ent = e["ent2_str"]["value"].split("/")[-1]

            elif wiki_id == ent1_wiki:
                rel_type = "supported_by"
                other_ent_url = ent2_wiki
                other_ent_name = e["ent2_str"]["value"].split("/")[-1]
                focus_ent = e["ent1_str"]["value"].split("/")[-1]

        elif e["rel_type"]["value"] == "ent2_opposes_ent1":

            if wiki_id == ent2_wiki:
                rel_type = "opposes"
                other_ent_url = ent1_wiki
                other_ent_name = e["ent1_str"]["value"].split("/")[-1]
                focus_ent = e["ent2_str"]["value"].split("/")[-1]

            elif wiki_id == ent1_wiki:
                rel_type = "opposed_by"
                other_ent_url = ent2_wiki
                other_ent_name = e["ent2_str"]["value"].split("/")[-1]
                focus_ent = e["ent1_str"]["value"].split("/")[-1]

        elif e["rel_type"]["value"] == "ent1_other_ent2":

            if wiki_id == ent1_wiki:
                rel_type = "other"
                other_ent_url = ent2_wiki
                other_ent_name = e["ent2_str"]["value"].split("/")[-1]
                focus_ent = e["ent1_str"]["value"].split("/")[-1]

            elif wiki_id == ent2_wiki:
                rel_type = "other_by"
                other_ent_url = ent1_wiki
                other_ent_name = e["ent1_str"]["value"].split("/")[-1]
                focus_ent = e["ent2_str"]["value"].split("/")[-1]

        elif e["rel_type"]["value"] == "ent2_other_ent1":

            if wiki_id == ent2_wiki:
                rel_type = "other"
                other_ent_url = ent1_wiki
                other_ent_name = e["ent1_str"]["value"].split("/")[-1]
                focus_ent = e["ent2_str"]["value"].split("/")[-1]

            elif wiki_id == ent1_wiki:
                rel_type = "other_by"
                other_ent_url = ent2_wiki
                other_ent_name = e["ent2_str"]["value"].split("/")[-1]
                focus_ent = e["ent1_str"]["value"].split("/")[-1]

        else:
            raise Exception(e["rel_type"]["value"] + " not known")

        relations[rel_type].append(
            {
                "url": e["arquivo_doc"]["value"],
                "title": e["title"]["value"],
                "score": str(e["score"]["value"])[0:5],
                "date": e["date"]["value"].split("T")[0],
                "focus_ent": focus_ent,
                "other_ent_url": "entity?q=" + other_ent_url,
                "other_ent_name": other_ent_name,
            }
        )

    return relations


@lru_cache
def get_top_relationships(wiki_id: str):
    persons_ent1 = defaultdict(list)
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
    results = query_sparql(prefixes + "\n" + query, "politiquices")
    for x in results["results"]["bindings"]:
        persons_ent1[x["rel_type"]["value"]].append(
            {
                "wiki_id": x["ent2"]["value"].split("/")[-1],
                "name": x["ent2_name"]["value"],
                "nr_articles": int(x["nr_articles"]["value"]),
            }
        )

    persons_ent2 = defaultdict(list)
    query = f"""
        SELECT ?rel_type ?ent1 ?ent1_name (COUNT(?arquivo_doc) as ?nr_articles)
        WHERE {{ 
          ?rel my_prefix:ent1 ?ent1  .
          ?ent1 rdfs:label ?ent1_name .
          ?rel my_prefix:ent2 wd:{wiki_id}  .
          ?rel my_prefix:type ?rel_type .
          ?rel my_prefix:arquivo ?arquivo_doc .
          FILTER(?rel_type != "other")
        }}
        GROUP BY ?rel_type ?ent1 ?ent1_name
        ORDER BY ?rel_type DESC(?nr_articles)
        """
    results = query_sparql(prefixes + "\n" + query, "politiquices")
    for x in results["results"]["bindings"]:
        persons_ent2[x["rel_type"]["value"]].append(
            {
                "wiki_id": x["ent1"]["value"].split("/")[-1],
                "name": x["ent1_name"]["value"],
                "nr_articles": int(x["nr_articles"]["value"]),
            }
        )

    who_person_opposes = [x for x in persons_ent1["ent1_opposes_ent2"]]
    who_person_supports = [x for x in persons_ent1["ent1_supports_ent2"]]
    who_opposes_person = [x for x in persons_ent2["ent1_opposes_ent2"]]
    who_supports_person = [x for x in persons_ent2["ent1_supports_ent2"]]

    return {
        "who_person_opposes": who_person_opposes,
        "who_person_supports": who_person_supports,
        "who_opposes_person": who_opposes_person,
        "who_supports_person": who_supports_person,
    }


@lru_cache
def get_person_rels_by_month_year(wiki_id, rel_type, ent="ent1"):
    query = f"""
        SELECT DISTINCT ?year ?month (COUNT(?arquivo_doc) as ?nr_articles)
        WHERE {{

              ?rel my_prefix:{ent} wd:{wiki_id} .
              ?rel my_prefix:type ?rel_type ;
                   my_prefix:score ?score.

              FILTER (?rel_type = "{rel_type}")

              ?rel my_prefix:ent1 ?ent1 ;
                   my_prefix:ent2 ?ent2 ;
                   my_prefix:ent1_str ?ent1_str ;
                   my_prefix:ent2_str ?ent2_str ;
                   my_prefix:arquivo ?arquivo_doc .
            
              ?arquivo_doc dc:title ?title ;
                           dc:date  ?date .
        }}
    GROUP BY (YEAR(?date) AS ?year) (MONTH(?date) AS ?month)
    ORDER BY ?year
    """
    result = query_sparql(prefixes + "\n" + query, "politiquices")

    # dicts are insertion ordered
    year_month_articles = dict()
    for x in result["results"]["bindings"]:
        year = x["year"]["value"]
        month = x["month"]["value"]
        year_month_articles[(str(year) + "-" + str(month))] = int(x["nr_articles"]["value"])

    return year_month_articles


def get_person_rels_by_year(wiki_id, rel_type, ent="ent1"):
    query = f"""
        SELECT DISTINCT ?year (COUNT(?arquivo_doc) as ?nr_articles)
        WHERE {{

              ?rel my_prefix:{ent} wd:{wiki_id} .
              ?rel my_prefix:type ?rel_type ;
                   my_prefix:score ?score.

              FILTER (?rel_type = "{rel_type}")

              ?rel my_prefix:ent1 ?ent1 ;
                   my_prefix:ent2 ?ent2 ;
                   my_prefix:ent1_str ?ent1_str ;
                   my_prefix:ent2_str ?ent2_str ;
                   my_prefix:arquivo ?arquivo_doc .

              ?arquivo_doc dc:title ?title ;
                           dc:date  ?date .
        }}
    GROUP BY (YEAR(?date) AS ?year)
    ORDER BY ?year
    """
    result = query_sparql(prefixes + "\n" + query, "politiquices")
    # dicts are insertion ordered
    year_articles = dict()
    for x in result["results"]["bindings"]:
        year = x["year"]["value"]
        year_articles[str(year)] = int(x["nr_articles"]["value"])

    return year_articles


# relationship queries
@lru_cache
def get_relationships_between_two_entities(wiki_id_one, wiki_id_two):
    query = f"""
        SELECT DISTINCT ?arquivo_doc ?date ?title ?rel_type ?score ?ent1 ?ent1_str ?ent2 ?ent2_str
        WHERE {{
          {{
          ?rel my_prefix:ent1 wd:{wiki_id_one};
               my_prefix:ent2 wd:{wiki_id_two};       
               my_prefix:type ?rel_type;
               my_prefix:score ?score;
               my_prefix:arquivo ?arquivo_doc;
               my_prefix:ent1 ?ent1;
               my_prefix:ent2 ?ent2;
               my_prefix:ent1_str ?ent1_str;
               my_prefix:ent2_str ?ent2_str.
          ?arquivo_doc dc:title ?title ;
                       dc:date  ?date .
              }} UNION {{
          ?rel my_prefix:ent2 wd:{wiki_id_one};
               my_prefix:ent1 wd:{wiki_id_two};       
               my_prefix:type ?rel_type;
               my_prefix:score ?score;
               my_prefix:arquivo ?arquivo_doc;
               my_prefix:ent1 ?ent1;
               my_prefix:ent2 ?ent2;
               my_prefix:ent1_str ?ent1_str;
               my_prefix:ent2_str ?ent2_str.
          ?arquivo_doc dc:title ?title ;
                       dc:date  ?date .
            }}
        }}
        ORDER BY ASC(?date)
        """
    result = query_sparql(prefixes + "\n" + query, "politiquices")

    def relationships_counter():
        return {
            "ent1_opposes_ent2": 0,
            "ent1_supports_ent2": 0,
            "ent2_opposes_ent1": 0,
            "ent2_supports_ent1": 0,
        }
    rels_freq_by_year_ent1 = defaultdict(relationships_counter)
    rels_freq_by_year_ent2 = defaultdict(relationships_counter)

    relationships = []
    for x in result["results"]["bindings"]:
        if 'other' in x["rel_type"]["value"]:
            continue
        relationships.append(
            {
                "url": x["arquivo_doc"]["value"],
                "date": x["date"]["value"],
                "title": x["title"]["value"],
                "rel_type": x["rel_type"]["value"],
                "score": x["score"]["value"][0:5],
                "ent1": x["ent1"]["value"],
                "ent1_str": x["ent1_str"]["value"],
                "ent2": x["ent2"]["value"],
                "ent2_str": x["ent2_str"]["value"],
            }
        )

        ent1_wiki_id = x["ent1"]["value"].split("/")[-1]
        year = x["date"]["value"][0:4]
        rel_type = x["rel_type"]["value"]

        if ent1_wiki_id == wiki_id_one:
            rels_freq_by_year_ent1[year][rel_type] += 1

        if ent1_wiki_id == wiki_id_two:
            rels_freq_by_year_ent2[year][rel_type] += 1

    return relationships, rels_freq_by_year_ent1, rels_freq_by_year_ent2


@lru_cache
def list_of_spec_relations_between_members_of_a_party_with_someone(party, person, relation):
    query = f"""        
        SELECT DISTINCT ?ent1 ?ent1_str ?ent2_str ?arquivo_doc ?date ?title ?score
        WHERE {{
            ?rel my_prefix:type '{relation}';
                 my_prefix:ent1 ?ent1;
                 my_prefix:ent1_str ?ent1_str;
                 my_prefix:ent2 wd:{person};                                              
                 my_prefix:ent2_str ?ent2_str;                 
                 my_prefix:score ?score;
                 my_prefix:arquivo ?arquivo_doc .            
            
            ?arquivo_doc dc:title ?title;
                         dc:date ?date.
        
            SERVICE <{wikidata_endpoint}> {{
                ?ent1 wdt:P102 wd:{party};
                      rdfs:label ?personLabel.
                FILTER(LANG(?personLabel) = "pt")                
            }}
        }}
        ORDER BY DESC(?date) ASC(?score)
        """

    result = query_sparql(prefixes + "\n" + query, "politiquices")
    results = []
    for x in result["results"]["bindings"]:
        results.append(
            {
                "url": x["arquivo_doc"]["value"],
                "date": x["date"]["value"],
                "title": x["title"]["value"],
                "rel_type": relation,
                "score": x["score"]["value"][0:5],
                "ent1": x["ent1"]["value"],
                "ent1_str": x["ent1_str"]["value"],
                "ent2": person,
                "ent2_str": x["ent2_str"]["value"],
            }
        )

    return results


@lru_cache
def list_of_spec_relations_between_a_person_and_members_of_a_party(person, party, relation):
    query = f"""        
        SELECT DISTINCT ?ent2 ?ent2_str ?ent1_str ?arquivo_doc ?date ?title ?score
        WHERE {{
            
            ?rel my_prefix:type '{relation}';
                 my_prefix:ent1 wd:{person};
                 my_prefix:ent1_str ?ent1_str;
                 my_prefix:ent2 ?ent2;
                 my_prefix:ent2_str ?ent2_str;
                 my_prefix:score ?score;
                 my_prefix:arquivo ?arquivo_doc .
            
            ?arquivo_doc dc:title ?title;
                         dc:date ?date.
            
            SERVICE <{wikidata_endpoint}> {{
                ?ent2 wdt:P102 wd:{party};
                      rdfs:label ?personLabel.
                FILTER(LANG(?personLabel) = "pt")                
            }}
        }}
        ORDER BY DESC(?date) ASC(?score)
        """

    result = query_sparql(prefixes + "\n" + query, "politiquices")
    results = []
    for x in result["results"]["bindings"]:
        results.append(
            {
                "url": x["arquivo_doc"]["value"],
                "date": x["date"]["value"],
                "title": x["title"]["value"],
                "rel_type": relation,
                "score": x["score"]["value"][0:5],
                "ent1": person,
                "ent1_str": x["ent1_str"]["value"],
                "ent2": x["ent2"]["value"],
                "ent2_str": x["ent2_str"]["value"],
            }
        )

    return results


@lru_cache
def list_of_spec_relations_between_two_parties(values_party_a, values_party_b, relation):
    query = f"""
    SELECT DISTINCT ?person_party_a ?ent1_str ?person_party_b ?ent2_str 
                    ?arquivo_doc ?date ?title ?rel_type ?score
    WHERE {{
      {{
        
        VALUES ?person_party_a {{ {values_party_a} }}
        VALUES ?person_party_b {{ {values_party_b} }}
        
        ?rel my_prefix:type '{relation}';
             my_prefix:ent1 ?person_party_a;
             my_prefix:ent1_str ?ent1_str;
             my_prefix:ent2 ?person_party_b;
             my_prefix:ent2_str ?ent2_str;
             
             my_prefix:score ?score;
             my_prefix:arquivo ?arquivo_doc.
        
        ?arquivo_doc dc:title ?title;
                     dc:date ?date.             
        }}
      }}
    """

    result = query_sparql(prefixes + "\n" + query, "politiquices")
    relationships = []
    for x in result["results"]["bindings"]:
        relationships.append(
            {
                "url": x["arquivo_doc"]["value"],
                "date": x["date"]["value"],
                "title": x["title"]["value"],
                "rel_type": relation,
                "score": x["score"]["value"][0:5],
                "ent1": x["person_party_a"]["value"],
                "ent1_str": x["ent1_str"]["value"],
                "ent2": x["person_party_b"]["value"],
                "ent2_str": x["ent2_str"]["value"],
            }
        )
    return relationships


# Other #
def get_entities_without_image():
    query = f"""
        SELECT DISTINCT ?item ?label ?image_url {{
            ?item wdt:P31 wd:Q5.
                SERVICE <{live_wikidata}> {{
                ?item rdfs:label ?label .
                FILTER(LANG(?label) = "pt")
                FILTER NOT EXISTS {{ ?item wdt:P18 ?image_url. }}
          }}
          }}
        ORDER BY ?label
        """
    result = query_sparql(prefixes + "\n" + query, "politiquices")
    entities = []
    for x in result["results"]["bindings"]:
        entities.append(
            {"wikidata_id": x["item"]["value"].split("/")[-1], "label": x["label"]["value"]}
        )
    print(len(entities), "entities retrieved")
    return entities


def query_sparql(query, endpoint):
    if endpoint == "wikidata":
        endpoint_url = wikidata_endpoint

    elif endpoint == "politiquices":
        endpoint_url = "http://0.0.0.0:3030/politiquices/query"

    # ToDo: see user agent policy: https://w.wiki/CX6
    user_agent = "Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results
