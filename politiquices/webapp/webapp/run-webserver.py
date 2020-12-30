#!/usr/bin/env python
import json

from app import app

from politiquices.webapp.webapp.app.sparql_queries import query_sparql
from politiquices.webapp.webapp.app.sparql_queries import all_entities
from politiquices.webapp.webapp.app.sparql_queries import get_total_nr_articles_for_each_person
from politiquices.webapp.webapp.app.sparql_queries import prefixes

ps_logo = "/static/images/Logo_do_Partido_Socialista(Portugal).png"
no_image = "/static/images/no_picture.jpg"
static_data = 'webapp/app/static/'
wikidata_endpoint = "http://0.0.0.0:3030/wikidata/query"


def get_persons():
    persons_query = """
        SELECT DISTINCT ?personLabel ?item ?image_url {
            ?item wdt:P31 wd:Q5 # get all human entities from the local graph
            SERVICE <http://0.0.0.0:3030/wikidata/query> {
                OPTIONAL { ?item wdt:P18 ?image_url. }
                ?item rdfs:label ?personLabel FILTER(LANG(?personLabel)="pt") .
            }
        }
        ORDER BY ?personLabel
        """
    result = query_sparql(prefixes + "\n" + persons_query, "politiquices")
    persons = []
    seen = set()
    for x in result["results"]["bindings"]:
        wikid_id = x["item"]["value"].split("/")[-1]
        if wikid_id in seen:
            continue

        image_url = None

        if "image_url" in x:
            image_url = x["image_url"]["value"]

        persons.append(
            {
                "wiki_id": wikid_id,
                "name": x["personLabel"]["value"],
                "image_url": image_url,
            }
        )
        seen.add(x["item"]["value"].split("/")[-1])

    return persons


def get_parties():
    parties_query = """
    SELECT DISTINCT ?political_party ?party_label ?party_logo (COUNT(?person) as ?nr_personalities) 
    {
        ?person wdt:P31 wd:Q5 .
        SERVICE <http://0.0.0.0:3030/wikidata/query> {
            ?person wdt:P102 ?political_party .
            ?political_party rdfs:label ?party_label .
            OPTIONAL {?political_party wdt:P154 ?party_logo. }
            FILTER(LANG(?party_label) = "pt")
      }
    } 
    GROUP BY ?political_party ?party_label ?party_logo
    HAVING (COUNT(?person) > 2)
    ORDER BY DESC(?nr_personalities)
    """
    result = query_sparql(prefixes + "\n" + parties_query, "politiquices")
    persons = []
    seen = set()
    for x in result["results"]["bindings"]:

        wikid_id = x["political_party"]["value"].split("/")[-1]
        if wikid_id in seen:
            continue

        image_url = None

        if "party_logo" in x:
            image_url = x["party_logo"]["value"]

        persons.append(
            {
                "wiki_id": wikid_id,
                "name": x["party_label"]["value"],
                "image_url": image_url,
            }
        )
        seen.add(x["political_party"]["value"].split("/")[-1])

    return persons


def get_entities():
    entities = query_sparql(all_entities(), "politiquices")
    persons = set()
    items_as_dict = dict()
    nr_entities = len(entities["results"]["bindings"])
    print(f"{nr_entities} retrieved")
    for e in entities["results"]["bindings"]:
        # this is just avoid duplicate entities, same entity with two labels
        url = e["item"]["value"]
        if url in persons:
            continue
        persons.add(url)
        name = e["label"]["value"]
        image_url = e["image_url"]["value"] if "image_url" in e else no_image
        wiki_id = url.split("/")[-1]
        items_as_dict[wiki_id] = {
            "wikidata_url": url,
            "wikidata_id": wiki_id,
            "name": name,
            "nr_articles": 0,
            "image_url": image_url,
        }
    article_counts = query_sparql(get_total_nr_articles_for_each_person(), "politiquices")
    for e in article_counts["results"]["bindings"]:
        wiki_id = e["person"]["value"].split("/")[-1]
        if wiki_id in items_as_dict:
            nr_articles = int(e["count"]["value"])
            items_as_dict[wiki_id]["nr_articles"] = nr_articles
    items = sorted(list(items_as_dict.values()), key=lambda x: x["nr_articles"], reverse=True)

    return items


def get_all_parties():
    query = f"""
        SELECT DISTINCT ?political_party ?party_label ?party_logo 
                        (COUNT(?person) as ?nr_personalities){{
            ?person wdt:P31 wd:Q5 .
            SERVICE <{wikidata_endpoint}> {{
                ?person wdt:P102 ?political_party .
                ?political_party rdfs:label ?party_label .
                OPTIONAL {{?political_party wdt:P154 ?party_logo. }} 
                FILTER(LANG(?party_label) = "pt")
          }}
        }} GROUP BY ?political_party ?party_label ?party_logo
        ORDER BY DESC(?nr_personalities)
        """

    results = query_sparql(prefixes + "\n" + query, "politiquices")
    political_parties = []
    for x in results["results"]["bindings"]:

        if "party_logo" in x:
            party_logo = x["party_logo"]["value"]
        else:
            if x["political_party"]["value"].split("/")[-1] == "Q847263":
                party_logo = ps_logo
            else:
                party_logo = no_image
        political_parties.append(
            {
                "wiki_id": x["political_party"]["value"].split("/")[-1],
                "party_label": x["party_label"]["value"],
                "party_logo": party_logo,
                "nr_personalities": x["nr_personalities"]["value"],
            }
        )

    return political_parties


def main():

    print("\nCaching static stuff from SPARQL engine :-)")
    data = get_persons()
    print(f'{len(data)} persons found (search boxes)')
    with open(static_data+"persons.json", "wt") as f_out:
        json.dump(data, f_out, indent=True, sort_keys="True")

    data = get_parties()
    print(f'{len(data)} parties found (search boxes)')
    with open(static_data+"parties.json", "wt") as f_out:
        json.dump(data, f_out, indent=True, sort_keys="True")

    data = get_entities()
    print(f"{len(data)} entities card info (positions + wikidata_link + image + nr articles)")
    with open(static_data+"all_entities.json", 'wt') as f_out:
        json.dump(data, f_out, indent=4)

    data = get_all_parties()
    print(f"{len(data)} parties info (image + nr affiliated personalities)")
    with open(static_data+"all_parties_info.json", 'wt') as f_out:
        json.dump(data, f_out, indent=4)

    app.run(debug=True, host='0.0.0.0')


if __name__ == '__main__':
    main()
