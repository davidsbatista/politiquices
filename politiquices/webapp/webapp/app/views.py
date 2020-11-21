import logging

from flask import request
from flask import render_template
from app import app

from politiquices.webapp.webapp.app.sparql_queries import (
    query_sparql,
    get_total_nr_articles_for_each_person,
    get_nr_articles_per_year,
    get_nr_of_persons,
    get_total_nr_of_articles,
    get_person_info,
    get_list_of_persons_from_some_party_opposing_someone,
    get_persons_affiliated_with_party)
from politiquices.webapp.webapp.app.sparql_queries import initalize
from politiquices.webapp.webapp.app.relationships import (
    build_list_relationships_articles,
    build_relationships_freq,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

cached_list_entities = None
person_no_image = "/static/images/no_picture.jpg"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search')
def search():
    return render_template('search.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route("/stats")
def status():
    year, nr_articles_year = get_nr_articles_per_year()
    nr_persons = get_nr_of_persons()
    nr_articles = get_total_nr_of_articles()
    items = {
        "nr_persons": nr_persons,
        "nr_articles": nr_articles,
        "year_labels": year,
        "year_articles": nr_articles_year,
    }
    return render_template("stats.html", items=items)


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
            image_url = e["image_url"]["value"] if "image_url" in e else person_no_image

            wiki_id = url.split("/")[-1]

            items_as_dict[wiki_id] = {
                "wikidata_url": url,
                "wikidata_id": wiki_id,
                "name": name,
                "nr_articles": 0,
                "image_url": image_url,
            }

        article_counts = query_sparql(get_total_nr_articles_for_each_person(), "local")
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
    person = get_person_info(wiki_id)
    opposed, supported, opposed_by, supported_by = build_list_relationships_articles(wiki_id)

    (
        year_month_labels,
        opposed_freq,
        supported_freq,
        opposed_by_freq,
        supported_by_freq,
    ) = build_relationships_freq(wiki_id)

    items = {
        "wiki_id": person.wiki_id,
        "name": person.name,
        "image": person.image_url,
        "parties": person.parties,
        "offices": person.positions,
        "opposed": opposed,
        "supported": supported,
        "opposed_by": opposed_by,
        "supported_by": supported_by,
        "year_month_labels": year_month_labels,
        "opposed_freq": opposed_freq,
        "supported_freq": supported_freq,
        "opposed_by_freq": opposed_by_freq,
        "supported_by_freq": supported_by_freq,
    }

    return render_template("entity.html", items=items)


@app.route("/party")
def party_members():
    wiki_id = request.args.get("q")
    items = get_persons_affiliated_with_party(wiki_id)
    return render_template("party_members.html", items=items)


@app.route('/queries')
def queries():
    query_nr = request.args.get("q")
    results = get_list_of_persons_from_some_party_opposing_someone()
    return render_template("template_one.html", items=results)
