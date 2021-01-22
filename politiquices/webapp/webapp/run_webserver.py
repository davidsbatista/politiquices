#!/usr/bin/env python
import json
from collections import defaultdict

from app import app

from politiquices.webapp.webapp.app.sparql_queries import prefixes, get_graph_links
from politiquices.webapp.webapp.app.sparql_queries import top_co_occurrences
from politiquices.webapp.webapp.app.sparql_queries import all_entities
from politiquices.webapp.webapp.app.sparql_queries import query_sparql
from politiquices.webapp.webapp.app.sparql_queries import get_wiki_id_affiliated_with_party
from politiquices.webapp.webapp.app.sparql_queries import get_total_nr_articles_for_each_person

ps_logo = "/static/images/Logo_do_Partido_Socialista(Portugal).png"
no_image = "/static/images/no_picture.jpg"
static_data = "webapp/app/static/json/"
wikidata_endpoint = "http://0.0.0.0:3030/wikidata/query"


def get_entities():
    # get all persons: name +  image url + wikidata url + wikidata id + nr articles
    entities = query_sparql(all_entities(), "politiquices")
    persons = set()
    items_as_dict = dict()
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
            "wiki_id": wiki_id,
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


def get_all_parties_with_affiliated_count():
    query = f"""
        SELECT DISTINCT ?political_party ?party_label ?party_logo ?country_label
                (COUNT(?person) as ?nr_personalities){{
            ?person wdt:P31 wd:Q5 .
            SERVICE <{wikidata_endpoint}> {{
                ?person wdt:P102 ?political_party .
                ?political_party rdfs:label ?party_label .
                OPTIONAL {{
                    ?political_party p:P17 ?country_stmt .
                    ?country_stmt ps:P17 ?country .
                    ?country rdfs:label ?country_label .
                }}
                FILTER(LANG(?country_label) = "pt")
                OPTIONAL {{?political_party wdt:P154 ?party_logo. }} 
                FILTER(LANG(?party_label) = "pt")
          }}
        }} 
        GROUP BY ?political_party ?party_label ?party_logo ?country_label
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
                "party_country": x["country_label"]["value"],
                "nr_personalities": x["nr_personalities"]["value"],
            }
        )

    return political_parties


def graph_edges_cache():
    edges = get_graph_links()
    with open(static_data + "edges.json", "w") as f_out:
        json.dump(edges, f_out, indent=4)
    print(f"{len(edges)} graph edges extracted")


def entities_top_co_occurrences(wiki_id):
    raw_counts = top_co_occurrences()
    co_occurrences = []
    for x in raw_counts:
        co_occurrences.append(
            {'person_a': wiki_id[x["person_a"].split("/")[-1]],
             'person_b': wiki_id[x["person_b"].split("/")[-1]],
             'nr_occurrences': x["n_artigos"]}
        )
    with open(static_data + "top_co_occurrences.json", "w") as f_out:
        json.dump(co_occurrences, f_out, indent=4)
    print(f"{len(co_occurrences)} entity co-ocorruences")


def parties_json_cache(all_politiquices_persons):

    # parties cache
    parties_data = get_all_parties_with_affiliated_count()
    print(f"{len(parties_data)} parties info (image + nr affiliated personalities)")
    with open(static_data + "all_parties_info.json", "w") as f_out:
        json.dump(parties_data, f_out, indent=4)

    # parties cache for search box, filtering only portuguese political parties
    parties = [
        {"name": x["party_label"], "wiki_id": x["wiki_id"], "image_url": x["party_logo"]}
        for x in sorted(parties_data, key=lambda x: x["party_label"])
        if x["party_country"] == 'Portugal'
    ]
    with open(static_data + "parties.json", "w") as f_out:
        json.dump(parties, f_out, indent=4)

    # members of each party
    party_members = defaultdict(list)
    for party in parties_data:
        # get all wiki_id associated with a party
        wiki_ids = get_wiki_id_affiliated_with_party(party["wiki_id"])
        # then filter only those with mention in new articles
        wiki_ids_in_politiquices = list(set(wiki_ids).intersection(all_politiquices_persons))
        party_members[party["wiki_id"]] = wiki_ids_in_politiquices
    with open(static_data + "party_members.json", "w") as f_out:
        json.dump(party_members, f_out, indent=4)


def personalities_json_cache():
    # persons cache
    per_data = get_entities()
    # mapping: wiki_id -> person_info
    wiki_id = {x["wiki_id"]: {"name": x["name"], "image_url": x["image_url"]} for x in per_data}
    with open(static_data + "wiki_id_info.json", "w") as f_out:
        json.dump(wiki_id, f_out, indent=4)
    print(f"{len(per_data)} entities card info (positions + wikidata_link + image + nr articles)")
    with open(static_data + "all_entities_info.json", "w") as f_out:
        json.dump(per_data, f_out, indent=4)
    # persons cache for search box
    persons = [
        {"name": x["name"], "wiki_id": x["wiki_id"], "image_url": x["image_url"]}
        for x in sorted(per_data, key=lambda x: x["name"])
    ]
    all_politiquices_persons = set([x["wiki_id"] for x in persons])
    with open(static_data + "persons.json", "wt") as f_out:
        json.dump(persons, f_out, indent=True)
    return all_politiquices_persons, wiki_id


def main():
    print("\nCaching static stuff from SPARQL engine :-)")

    # personalities cache
    all_politiquices_persons, wiki_id = personalities_json_cache()

    # parties cache
    parties_json_cache(all_politiquices_persons)

    # entities co-occurrences cache
    entities_top_co_occurrences(wiki_id)

    # graph edges cache
    graph_edges_cache()

    app.run(debug=True, host="0.0.0.0")


if __name__ == "__main__":
    main()
