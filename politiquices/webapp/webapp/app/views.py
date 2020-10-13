import logging
from datetime import datetime

from flask import request
from flask import render_template
from app import app

from politiquices.webapp.webapp.app.sparql_queries import (
    query_sparql,
    counts,
    nr_articles_per_year,
    nr_of_persons,
    total_nr_of_articles,
    get_all_relationships,
    get_all_relationships_by_month_year,
)
from politiquices.webapp.webapp.app.sparql_queries import initalize


def convert_dates(date: str):
    date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime("%Y %b")


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

cached_list_entities = None


@app.route("/")
def status():
    year, nr_articles_year = nr_articles_per_year()
    nr_persons = nr_of_persons()
    nr_articles = total_nr_of_articles()
    items = {
        "nr_persons": nr_persons,
        "nr_articles": nr_articles,
        "year_labels": year,
        "year_articles": nr_articles_year,
    }
    return render_template("index.html", items=items)


@app.route("/entities")
def list_entities():
    global cached_list_entities
    """
    ToDo: run this on the Makefile, just after the server is launched and cache
    """

    if not cached_list_entities:
        print("Getting entities extra info from wikidata.org")
        entities = query_sparql(initalize(), "local")
        persons = set()
        items_as_dict = dict()
        nr_entities = len(entities["results"]["bindings"])

        print(f"{nr_entities} retrieved")

        for e in entities["results"]["bindings"]:

            # this is just avoid duplicate entities, same entity with two labels
            # ToDo: see how to fix this with a SPARQL query
            url = e["item"]["value"]
            if url in persons:
                continue
            persons.add(url)

            name = e["label"]["value"]
            if "image_url" in e:
                image_url = e["image_url"]["value"]
            else:
                image_url = "/static/images/no_picture.jpg"

            wiki_id = url.split("/")[-1]

            items_as_dict[wiki_id] = {
                "wikidata_url": url,
                "wikidata_id": wiki_id,
                "name": name,
                "nr_articles": 0,
                "image_url": image_url,
            }

        article_counts = query_sparql(counts(), "local")
        for e in article_counts["results"]["bindings"]:
            wiki_id = e["person"]["value"].split("/")[-1]
            nr_articles = int(e["count"]["value"])
            items_as_dict[wiki_id]["nr_articles"] = nr_articles

        items = sorted(list(items_as_dict.values()), key=lambda x: x["nr_articles"], reverse=True)
        cached_list_entities = items

    else:
        items = cached_list_entities

    return render_template("all_entities.html", items=items)


@app.route("/entity")
def detail_entity():
    wiki_id = request.args.get("q")

    opposed = get_all_relationships(wiki_id, "ent1_opposes_ent2")
    supported = get_all_relationships(wiki_id, "ent1_supports_ent2")
    opposed_by = get_all_relationships(wiki_id, "ent1_opposes_ent2", reverse=True)
    supported_by = get_all_relationships(wiki_id, "ent1_supports_ent2", reverse=True)

    # ToDo: see https://www.chartjs.org/samples/latest/scales/time/financial.html
    #           https://www.chartjs.org/docs/latest/axes/cartesian/time.html
    #      - get first and last year-month of occurrence
    #      - fill-in all year-month within that interval that don't have any articles with 0
    opposed_freq = get_all_relationships_by_month_year(wiki_id, "ent1_opposes_ent2")
    supported_freq = get_all_relationships_by_month_year(wiki_id, "ent1_supports_ent2")
    opposed_by_freq = get_all_relationships_by_month_year(
        wiki_id, "ent1_opposes_ent2", reverse=True
    )
    supported_by_freq = get_all_relationships_by_month_year(
        wiki_id, "ent1_supports_ent2", reverse=True
    )

    # entity info
    query = f"""SELECT DISTINCT ?image_url ?officeLabel ?start ?end
                WHERE {{
                wd:{wiki_id} wdt:P18 ?image_url;
                             p:P39 ?officeStmnt.
                ?officeStmnt ps:P39 ?office.
                OPTIONAL {{ ?officeStmnt pq:P580 ?start. }}
                OPTIONAL {{ ?officeStmnt pq:P582 ?end. }}
                SERVICE wikibase:label {{ 
                    bd:serviceParam wikibase:language "pt". }}
                }} ORDER BY ?start"""
    results = query_sparql(query, "wiki")
    image_url = None
    offices = []
    for e in results["results"]["bindings"]:
        if not image_url:
            image_url = e["image_url"]["value"]
        start = None
        end = None
        if "start" in e:
            start = convert_dates(e["start"]["value"])
        if "end" in e:
            end = convert_dates(e["end"]["value"])

        offices.append({"title": e["officeLabel"]["value"], "start": start, "end": end})

    items = {
        "wiki_id": wiki_id,
        "image": image_url,
        "offices": offices,
        "opposed": opposed,
        "supported": supported,
        "opposed_by": opposed_by,
        "supported_by": supported_by,
    }

    return render_template("entity_detail.html", items=items)
