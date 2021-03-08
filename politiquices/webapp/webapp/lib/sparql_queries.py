import sys
from typing import Tuple, List
from collections import defaultdict

from SPARQLWrapper import SPARQLWrapper, JSON
from politiquices.webapp.webapp.lib.data_models import OfficePosition, Person, PoliticalParty
from politiquices.webapp.webapp.config import (
    wikidata_endpoint,
    no_image,
    ps_logo,
    live_wikidata,
    politiquices_endpoint,
)

POLITIQUICES_PREFIXES = """
    PREFIX politiquices: <http://www.politiquices.pt/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX		 ns2: <http://www.w3.org/2004/02/skos/core#>
    """

WIKIDATA_PREFIXES = """
    PREFIX        wd: <http://www.wikidata.org/entity/>
    PREFIX       wds: <http://www.wikidata.org/entity/statement/>
    PREFIX       wdv: <http://www.wikidata.org/value/>
    PREFIX       wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX         p: <http://www.wikidata.org/prop/>
    PREFIX        ps: <http://www.wikidata.org/prop/statement/>
    PREFIX        pq: <http://www.wikidata.org/prop/qualifier/>
    """

OTHERS = """
    PREFIX        bd: <http://www.bigdata.com/rdf#>
    PREFIX  wikibase: <http://wikiba.se/ontology#>
    """

PREFIXES = POLITIQUICES_PREFIXES + WIKIDATA_PREFIXES + OTHERS


# Statistics
def get_nr_articles_per_year() -> Tuple[List[int], List[int]]:
    query = """
        SELECT ?year (COUNT(?arquivo_doc) AS ?nr_articles)
        WHERE {
          ?x politiquices:url ?arquivo_doc .
          ?arquivo_doc dc:date ?date .
        }
        GROUP BY (YEAR(?date) AS ?year)
        ORDER BY ?year
        """
    result = query_sparql(PREFIXES + "\n" + query, "politiquices")
    year = []
    nr_articles = []
    for x in result["results"]["bindings"]:
        year.append(int(x["year"]["value"]))
        nr_articles.append(int(x["nr_articles"]["value"]))
    return year, nr_articles


def get_total_nr_of_articles() -> int:
    query = """
        SELECT (COUNT(?x) as ?nr_articles) WHERE {
            ?x politiquices:url ?y .
        }
        """
    results = query_sparql(PREFIXES + "\n" + query, "politiquices")
    return results["results"]["bindings"][0]["nr_articles"]["value"]


def get_nr_of_persons() -> int:

    # NOTE: persons with only 'ent1_other_ent2' and 'ent2_other_ent1' relationships
    #       are not considered

    query = """
        SELECT (COUNT(DISTINCT ?person) as ?nr_persons) {
            ?person wdt:P31 wd:Q5;
            {?rel politiquices:ent1 ?person} UNION {?rel politiquices:ent2 ?person} .
            ?rel politiquices:type ?rel_type FILTER(!REGEX(?rel_type,"other") ) .
        }
        """
    results = query_sparql(PREFIXES + "\n" + query, "politiquices")
    return results["results"]["bindings"][0]["nr_persons"]["value"]


def get_total_articles_by_year_by_relationship_type():
    query = """
        SELECT ?year ?rel_type (COUNT(?rel_type) AS ?nr_articles)
        WHERE {
            ?x politiquices:url ?arquivo_doc .
            ?x politiquices:type ?rel_type .
            ?arquivo_doc dc:date ?date .
        }
        GROUP BY (YEAR(?date) AS ?year) ?rel_type
        ORDER BY ?year
        """
    results = query_sparql(PREFIXES + "\n" + query, "politiquices")

    def rels_values():
        return {
            "ent1_opposes_ent2": 0,
            "ent2_opposes_ent1": 0,
            "ent1_supports_ent2": 0,
            "ent2_supports_ent1": 0,
            "ent1_other_ent2": 0,
            "ent2_other_ent1": 0,
        }

    values = defaultdict(rels_values)
    for x in results["results"]["bindings"]:
        values[x["year"]["value"]][x["rel_type"]["value"]] = x["nr_articles"]["value"]

    return values


# Cached in JSON files and load into memory on startup
def get_graph_edges():
    # NOTE: 'other' relationship types are ignored
    query = """
        SELECT DISTINCT ?person_a ?rel_type ?person_b ?date ?url {
        VALUES ?rel_values {'ent1_opposes_ent2' 'ent2_opposes_ent1' 
                            'ent1_supports_ent2' 'ent2_supports_ent1'} .
        ?rel politiquices:type ?rel_values .  
        ?rel politiquices:ent1 ?person_a .
        ?rel politiquices:ent2 ?person_b .        
        ?rel politiquices:type ?rel_type .
        ?rel politiquices:url ?url .
        ?url dc:date ?date .
        }
        """
    results = query_sparql(PREFIXES + "\n" + query, "politiquices")
    edges = [
        {
            "person_a": x["person_a"]["value"],
            "person_b": x["person_b"]["value"],
            "rel_type": x["rel_type"]["value"],
            "url": x["url"]["value"],
            "date": x["date"]["value"],
        }
        for x in results["results"]["bindings"]
    ]
    return edges


def get_persons_co_occurrences_counts():
    query = """
        SELECT DISTINCT ?person_a ?person_b (COUNT (?url) as ?n_artigos) {
            VALUES ?rel_values {'ent1_opposes_ent2' 'ent2_opposes_ent1' 
                                'ent1_supports_ent2' 'ent2_supports_ent1'} .

            ?rel politiquices:type ?rel_values .
            {
                ?rel politiquices:ent1 ?person_a .
                ?rel politiquices:ent2 ?person_b .
            }
            UNION {
                ?rel politiquices:ent2 ?person_a .
                ?rel politiquices:ent1 ?person_b .
            }
            ?rel politiquices:url ?url .
            ?rel politiquices:type ?rel_type .
        }
        GROUP BY ?person_a ?person_b
        ORDER BY DESC(?n_artigos)
        """
    results = query_sparql(PREFIXES + "\n" + query, "politiquices")
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


def get_persons_articles_freq():
    query = """
        SELECT DISTINCT ?person (COUNT (?url) as ?n_artigos) 
        WHERE {  
            VALUES ?rel_values {'ent1_opposes_ent2' 'ent2_opposes_ent1' 
                                'ent1_supports_ent2' 'ent2_supports_ent1'} .
                                
            ?rel politiquices:type ?rel_values .
            { ?rel politiquices:ent1 ?person .} UNION { ?rel politiquices:ent2 ?person . }              
            ?rel politiquices:url ?url .
            ?rel politiquices:type ?rel_type .
        }
        GROUP BY ?person
        HAVING (?n_artigos > 0)
        ORDER BY DESC(?n_artigos)
        """
    results = query_sparql(PREFIXES + "\n" + query, "politiquices")
    top_freq = [
        {"person": x["person"]["value"], "freq": x["n_artigos"]["value"]}
        for x in results["results"]["bindings"]
    ]
    return top_freq


def get_persons_wiki_id_name_image_url():
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
    return PREFIXES + "\n" + query


def get_total_nr_articles_for_each_person():
    # NOTE: 'ent1_other_ent2' and 'ent2_other_ent1' relationships are being discarded
    query = """
        SELECT ?person_name ?person (COUNT(*) as ?count){
          ?person wdt:P31 wd:Q5 ;
                  rdfs:label ?person_name .                    
          {?rel politiquices:ent1 ?person} UNION {?rel politiquices:ent2 ?person} .
          ?rel politiquices:type ?rel_type FILTER(!REGEX(?rel_type,"other") ) .
        }
        GROUP BY ?person_name ?person
        ORDER BY DESC (?count) ASC (?person_name)
        """
    return PREFIXES + "\n" + query


def get_nr_relationships_as_subject(relationship: str):
    query = f"""
        SELECT DISTINCT ?person_a (COUNT(?url) as ?nr_articles) {{
          {{ ?rel politiquices:ent1 ?person_a .
            ?rel politiquices:type 'ent1_{relationship}_ent2'.
          }}  
          UNION 
          {{ ?rel politiquices:ent2 ?person_a .
            ?rel politiquices:type 'ent2_{relationship}_ent1'.
          }}
          ?rel politiquices:url ?url .
        }}
        GROUP BY ?person_a
        ORDER BY DESC(?nr_articles)
        """
    results = query_sparql(PREFIXES + "\n" + query, "politiquices")
    return [
        (x["person_a"]["value"].split("/")[-1], int(x["nr_articles"]["value"]))
        for x in results["results"]["bindings"]
    ]


def get_nr_relationships_as_target(relationship: str):
    query = f"""
        SELECT DISTINCT ?person_a (COUNT(?url) as ?nr_articles) {{
          {{ ?rel politiquices:ent2 ?person_a .
            ?rel politiquices:type 'ent1_{relationship}_ent2'.
          }}  
          UNION 
          {{ ?rel politiquices:ent1 ?person_a .
            ?rel politiquices:type 'ent2_{relationship}_ent1'.
          }}
          ?rel politiquices:url ?url .
        }}
        GROUP BY ?person_a
        ORDER BY DESC(?nr_articles)
        """
    results = query_sparql(PREFIXES + "\n" + query, "politiquices")
    return [
        (x["person_a"]["value"].split("/")[-1], int(x["nr_articles"]["value"]))
        for x in results["results"]["bindings"]
    ]


# Parties
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
    results = query_sparql(PREFIXES + "\n" + query, "politiquices")
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
            Person(
                name=wiki_id,
                wiki_id=x["person"]["value"].split("/")[-1],
                image_url=image,
            )
        )
        seen.add(wiki_id)

    return persons, party_name, party_logo


def get_wiki_id_affiliated_with_party(political_party: str):
    query = f"""
        SELECT DISTINCT ?wiki_id {{
            ?wiki_id wdt:P102 wd:{political_party}; .  
        }}
    """
    results = query_sparql(PREFIXES + "\n" + query, "wikidata")
    return [x["wiki_id"]["value"].split("/")[-1] for x in results["results"]["bindings"]]


# Personality Information
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
    results = query_sparql(PREFIXES + "\n" + query, "wikidata")

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

    results = query_sparql(PREFIXES + "\n" + occupation_query, "wikidata")
    occupations = [x["occupation_label"]["value"] for x in results["results"]["bindings"]]

    results = query_sparql(PREFIXES + "\n" + education_query, "wikidata")
    education = [x["educatedAt_label"]["value"] for x in results["results"]["bindings"]]

    results = query_sparql(PREFIXES + "\n" + positions_query, "wikidata")
    positions = [x["position_label"]["value"] for x in results["results"]["bindings"]]

    return {"education": education, "occupation": occupations, "position": positions}


def get_person_relationships(wiki_id):
    query = f"""
        SELECT DISTINCT ?arquivo_doc ?date ?title ?rel_type ?score ?ent1 ?ent1_str ?ent2 ?ent2_str
        WHERE {{
         {{ ?rel politiquices:ent1 wd:{wiki_id} }} UNION {{?rel politiquices:ent2 wd:{wiki_id} }}        

            ?rel politiquices:type ?rel_type;
                 politiquices:score ?score.

             ?rel politiquices:ent1 ?ent1 ;
                  politiquices:ent2 ?ent2 ;
                  politiquices:ent1_str ?ent1_str ;
                  politiquices:ent2_str ?ent2_str ;
                  politiquices:url ?arquivo_doc .

              ?arquivo_doc dc:title ?title ;
                           dc:date  ?date .
        }}
        ORDER BY ASC(?date)
        """

    results = query_sparql(PREFIXES + "\n" + query, "politiquices")
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
                "rel_type": rel_type,
            }
        )

    return relations


def get_top_relationships(wiki_id: str):
    persons_ent1 = defaultdict(list)
    query = f"""
        SELECT ?rel_type ?ent2 ?ent2_name (COUNT(?arquivo_doc) as ?nr_articles)
        WHERE {{ 
          ?rel politiquices:ent1 wd:{wiki_id}  .
          ?rel politiquices:ent2 ?ent2 .
          ?ent2 rdfs:label ?ent2_name .
          ?rel politiquices:type ?rel_type .
          ?rel politiquices:url ?arquivo_doc .
          FILTER(?rel_type != "other")
        }} GROUP BY ?rel_type ?ent2 ?ent2_name
        ORDER BY ?rel_type DESC(?nr_articles)
        """
    results = query_sparql(PREFIXES + "\n" + query, "politiquices")
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
          ?rel politiquices:ent1 ?ent1  .
          ?ent1 rdfs:label ?ent1_name .
          ?rel politiquices:ent2 wd:{wiki_id}  .
          ?rel politiquices:type ?rel_type .
          ?rel politiquices:url ?arquivo_doc .
          FILTER(?rel_type != "other")
        }}
        GROUP BY ?rel_type ?ent1 ?ent1_name
        ORDER BY ?rel_type DESC(?nr_articles)
        """
    results = query_sparql(PREFIXES + "\n" + query, "politiquices")
    for x in results["results"]["bindings"]:
        persons_ent2[x["rel_type"]["value"]].append(
            {
                "wiki_id": x["ent1"]["value"].split("/")[-1],
                "name": x["ent1_name"]["value"],
                "nr_articles": int(x["nr_articles"]["value"]),
            }
        )

    return {
        "who_person_opposes": persons_ent1["ent1_opposes_ent2"],
        "who_person_supports": persons_ent1["ent1_supports_ent2"],
        "who_opposes_person": persons_ent2["ent1_opposes_ent2"],
        "who_supports_person": persons_ent2["ent1_supports_ent2"],
    }


def get_person_relationships_by_year(wiki_id, rel_type, ent="ent1"):
    query = f"""
        SELECT DISTINCT ?year (COUNT(?arquivo_doc) as ?nr_articles)
        WHERE {{

              ?rel politiquices:{ent} wd:{wiki_id} .
              ?rel politiquices:type ?rel_type ;
                   politiquices:score ?score.

              FILTER (?rel_type = "{rel_type}")

              ?rel politiquices:ent1 ?ent1 ;
                   politiquices:ent2 ?ent2 ;
                   politiquices:ent1_str ?ent1_str ;
                   politiquices:ent2_str ?ent2_str ;
                   politiquices:url ?arquivo_doc .

              ?arquivo_doc dc:title ?title ;
                           dc:date  ?date .
        }}
    GROUP BY (YEAR(?date) AS ?year)
    ORDER BY ?year
    """
    result = query_sparql(PREFIXES + "\n" + query, "politiquices")
    # dicts are insertion ordered
    year_articles = dict()
    for x in result["results"]["bindings"]:
        year = x["year"]["value"]
        year_articles[str(year)] = int(x["nr_articles"]["value"])

    return year_articles


# Relationship Queries
def get_relationship_between_two_persons(wiki_id_one, wiki_id_two, rel_type, start_year, end_year):
    query = f"""
        SELECT DISTINCT ?arquivo_doc ?date ?title ?rel_type ?score ?ent1 ?ent1_str ?ent2 ?ent2_str
        WHERE {{          
          ?rel politiquices:ent1 wd:{wiki_id_one};
               politiquices:ent2 wd:{wiki_id_two};       
               politiquices:type '{rel_type}';
               politiquices:score ?score;
               politiquices:url ?arquivo_doc;
               politiquices:ent1 ?ent1;
               politiquices:ent2 ?ent2;
               politiquices:ent1_str ?ent1_str;
               politiquices:ent2_str ?ent2_str.

          ?arquivo_doc dc:title ?title ;
                       dc:date ?date . FILTER(YEAR(?date)>={start_year} && YEAR(?date)<={end_year})
        }}
        ORDER BY ASC(?date)
        """

    result = query_sparql(PREFIXES + "\n" + query, "politiquices")
    results = []
    for x in result["results"]["bindings"]:
        results.append(
            {
                "url": x["arquivo_doc"]["value"],
                "date": x["date"]["value"],
                "title": x["title"]["value"],
                "score": x["score"]["value"][0:5],
                "rel_type": rel_type,
                "ent1_wiki": wiki_id_one,
                "ent1_str": x["ent1_str"]["value"],
                "ent2_wiki": x["ent2"]["value"],
                "ent2_str": x["ent2_str"]["value"],
            }
        )

    return results


def get_relationship_between_party_and_person(party, person, relation, start_year, end_year):
    query = f"""
        SELECT DISTINCT ?ent1 ?ent1_str ?ent2_str ?arquivo_doc ?date ?title ?score
        WHERE {{
            ?rel politiquices:type '{relation}';
                 politiquices:ent1 ?ent1;
                 politiquices:ent1_str ?ent1_str;
                 politiquices:ent2 wd:{person};                                              
                 politiquices:ent2_str ?ent2_str;                 
                 politiquices:score ?score;
                 politiquices:url ?arquivo_doc .            

            ?arquivo_doc dc:title ?title;
                         dc:date ?date. FILTER(YEAR(?date)>={start_year} && YEAR(?date)<={end_year})

            SERVICE <{wikidata_endpoint}> {{
                ?ent1 wdt:P102 wd:{party};
                      rdfs:label ?personLabel.
                FILTER(LANG(?personLabel) = "pt")                
            }}
        }}
        ORDER BY DESC(?date) ASC(?score)
        """

    result = query_sparql(PREFIXES + "\n" + query, "politiquices")
    results = []

    for x in result["results"]["bindings"]:
        results.append(
            {
                "url": x["arquivo_doc"]["value"],
                "date": x["date"]["value"],
                "title": x["title"]["value"],
                "rel_type": relation,
                "score": x["score"]["value"][0:5],
                "ent1_wiki": x["ent1"]["value"],
                "ent1_str": x["ent1_str"]["value"],
                "ent2_wiki": person,
                "ent2_str": x["ent2_str"]["value"],
            }
        )

    return results


def get_relationship_between_person_and_party(person, party, relation, start_year, end_year):
    query = f"""
        SELECT DISTINCT ?ent2 ?ent2_str ?ent1_str ?arquivo_doc ?date ?title ?score
        WHERE {{

            ?rel politiquices:type '{relation}';
                 politiquices:ent1 wd:{person};
                 politiquices:ent1_str ?ent1_str;
                 politiquices:ent2 ?ent2;
                 politiquices:ent2_str ?ent2_str;
                 politiquices:score ?score;
                 politiquices:url ?arquivo_doc .

            ?arquivo_doc dc:title ?title;
                         dc:date ?date; FILTER(YEAR(?date)>={start_year} && YEAR(?date)<={end_year})

            SERVICE <{wikidata_endpoint}> {{
                ?ent2 wdt:P102 wd:{party};
                      rdfs:label ?personLabel. FILTER(LANG(?personLabel) = "pt")                
            }}
        }}
        ORDER BY DESC(?date) ASC(?score)
        """
    result = query_sparql(PREFIXES + "\n" + query, "politiquices")
    results = []
    for x in result["results"]["bindings"]:
        results.append(
            {
                "url": x["arquivo_doc"]["value"],
                "date": x["date"]["value"],
                "title": x["title"]["value"],
                "rel_type": relation,
                "score": x["score"]["value"][0:5],
                "ent1_wiki": person,
                "ent1_str": x["ent1_str"]["value"],
                "ent2_wiki": x["ent2"]["value"],
                "ent2_str": x["ent2_str"]["value"],
            }
        )

    return results


def get_relationship_between_parties(per_party_a, per_party_b, relation, start_year, end_year):
    query = f"""
    SELECT DISTINCT ?person_party_a ?ent1_str ?person_party_b ?ent2_str ?arquivo_doc ?date ?title 
                    ?score
    WHERE {{
      {{ 
        VALUES ?person_party_a {{ {per_party_a} }}
        VALUES ?person_party_b {{ {per_party_b} }}
        ?rel politiquices:ent1 ?person_party_a;
             politiquices:ent2 ?person_party_b;
             politiquices:ent1_str ?ent1_str;
             politiquices:ent2_str ?ent2_str;
             {{ 
                SELECT ?rel ?arquivo_doc ?title ?date ?score
                WHERE {{
                      ?rel politiquices:type ?ent1_opposes_ent2;
                           politiquices:score ?score;
                           politiquices:url ?arquivo_doc.
                      ?arquivo_doc dc:title ?title;
                                   dc:date ?date; 
                                   FILTER(YEAR(?date)>={start_year} && YEAR(?date)<={end_year})
                }}
             }}
        }}
    }}
    """
    result = query_sparql(PREFIXES + "\n" + query, "politiquices")
    relationships = []
    for x in result["results"]["bindings"]:
        relationships.append(
            {
                "url": x["arquivo_doc"]["value"],
                "date": x["date"]["value"],
                "title": x["title"]["value"],
                "rel_type": relation,
                "score": x["score"]["value"][0:5],
                "ent1_wiki": x["person_party_a"]["value"],
                "ent1_str": x["ent1_str"]["value"],
                "ent2_wiki": x["person_party_b"]["value"],
                "ent2_str": x["ent2_str"]["value"],
            }
        )

    return relationships


def get_all_relationships_between_two_entities(wiki_id_one, wiki_id_two):
    query = f"""
        SELECT DISTINCT ?arquivo_doc ?date ?title ?rel_values ?score ?ent1 ?ent1_str ?ent2 ?ent2_str
        WHERE {{

              VALUES ?rel_values {{'ent1_opposes_ent2' 'ent2_opposes_ent1' 
                                  'ent1_supports_ent2' 'ent2_supports_ent1'}} 
              {{

              ?rel politiquices:ent1 wd:{wiki_id_one};
                   politiquices:ent2 wd:{wiki_id_two};
                   politiquices:ent1 ?ent1;
                   politiquices:ent2 ?ent2;
                   politiquices:ent1_str ?ent1_str;
                   politiquices:ent2_str ?ent2_str;
                   politiquices:type ?rel_values;
                   politiquices:score ?score;
                   politiquices:url ?arquivo_doc.

              ?arquivo_doc dc:title ?title;
                           dc:date  ?date .

              }} UNION {{

              ?rel politiquices:ent2 wd:{wiki_id_one};
                   politiquices:ent1 wd:{wiki_id_two};       
                   politiquices:ent2 ?ent2;
                   politiquices:ent1 ?ent1;
                   politiquices:ent2_str ?ent2_str;
                   politiquices:ent1_str ?ent1_str;
                   politiquices:type ?rel_values;
                   politiquices:score ?score;
                   politiquices:url ?arquivo_doc.                   

              ?arquivo_doc dc:title ?title;
                           dc:date  ?date .
                }}
        }}
        ORDER BY ASC(?date)
        """

    result = query_sparql(PREFIXES + "\n" + query, "politiquices")
    relationships = []
    for x in result["results"]["bindings"]:
        relationships.append(
            {
                "url": x["arquivo_doc"]["value"],
                "date": x["date"]["value"],
                "title": x["title"]["value"],
                "rel_type": x["rel_values"]["value"],
                "score": x["score"]["value"][0:5],
                "ent1_wiki": x["ent1"]["value"],
                "ent1_str": x["ent1_str"]["value"],
                "ent2_wiki": x["ent2"]["value"],
                "ent2_str": x["ent2_str"]["value"],
            }
        )

    return relationships


# Other
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
    result = query_sparql(PREFIXES + "\n" + query, "politiquices")
    entities = []
    for x in result["results"]["bindings"]:
        entities.append(
            {"wikidata_id": x["item"]["value"].split("/")[-1], "label": x["label"]["value"]}
        )

    return entities


# relationships to re-annotate, e.g 'other'
def get_relationships_to_annotate():
    query = """
        SELECT ?date ?url ?title ?rel_type ?score ?ent1 ?ent1_str ?ent2 ?ent2_str
        WHERE {
          ?x politiquices:type ?rel_type;
             politiquices:score ?score;
             politiquices:ent1 ?ent1;
             politiquices:ent2 ?ent2;
             politiquices:ent1_str ?ent1_str;
             politiquices:ent2_str ?ent2_str;
             politiquices:url ?url.

          ?url dc:date ?date ;
               dc:title ?title .

          FILTER(REGEX(?rel_type,"other")).
        }
        ORDER BY ?date ?score
        LIMIT 1000
    """
    result = query_sparql(PREFIXES + "\n" + query, "politiquices")
    to_annotate = []
    for x in result["results"]["bindings"]:
        to_annotate.append(
            {
                "date": x["date"]["value"],
                "url": x["url"]["value"],
                "title": x["title"]["value"],
                "rel_type": x["rel_type"]["value"],
                "score": x["score"]["value"][0:5],
                "ent1": x["ent1"]["value"],
                "ent1_str": x["ent1_str"]["value"],
                "ent2": x["ent2"]["value"],
                "ent2_str": x["ent2_str"]["value"],
            }
        )

    return to_annotate


def query_sparql(query, endpoint):
    if endpoint == "wikidata":
        endpoint_url = wikidata_endpoint

    elif endpoint == "politiquices":
        endpoint_url = politiquices_endpoint

    # ToDo: see user agent policy: https://w.wiki/CX6
    user_agent = "Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results