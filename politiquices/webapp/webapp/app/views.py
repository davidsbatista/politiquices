import json
import logging
from collections import defaultdict

from flask import request, jsonify
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
    get_persons_affiliated_with_party,
    get_top_relationships,
    get_all_parties,
    get_person_relationships,
    get_party_of_entity,
    get_list_of_persons_from_some_party_relation_with_someone,
    get_entities_without_image)
from politiquices.webapp.webapp.app.sparql_queries import initalize
from politiquices.webapp.webapp.app.relationships import build_relationships_freq

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

cached_list_entities = None
cached_all_parties = None
cached_members_parties = defaultdict(list)
cached_detailed_entity = defaultdict(list)
cached_party_name = defaultdict(str)
cached_party_logo = defaultdict(str)
person_no_image = "/static/images/no_picture.jpg"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/about")
def about():
    return render_template("about.html")


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
        entities = query_sparql(initalize(), "politiquices")
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

        article_counts = query_sparql(get_total_nr_articles_for_each_person(), "politiquices")
        for e in article_counts["results"]["bindings"]:
            wiki_id = e["person"]["value"].split("/")[-1]
            if wiki_id in items_as_dict:
                nr_articles = int(e["count"]["value"])
                items_as_dict[wiki_id]["nr_articles"] = nr_articles

        items = sorted(list(items_as_dict.values()), key=lambda x: x["nr_articles"], reverse=True)

        print(f"{nr_entities} entities mentioned in titles")

        cached_list_entities = items

    else:
        items = cached_list_entities

    return render_template("all_entities.html", items=items)


def make_title_linkable(r, wiki_id):
    # add link to focus entity
    link_one = r['title'].replace(
        r['focus_ent'],
        '<a id="ent_1" href="entity?q=' + wiki_id + '">' + r['focus_ent'] + '</a>'
    )
    # add link to other entity page
    title_link = link_one.replace(
        r['other_ent_name'],
        '<a id="ent_2" href=' + r['other_ent_url'] + '>' + r['other_ent_name'] + '</a>'
    )
    r['title_clickable'] = title_link
    if r['url'].startswith('http://publico.pt'):
        r['link_image'] = "/static/images/114px-Logo_publico.png"
        r['image_width'] = "20"
    else:
        r['link_image'] = "/static/images/color_vertical.svg"
        r['image_width'] = "39.8"


@app.route("/entity")
def detail_entity():
    from_search = False
    wiki_id = request.args.get("q")
    if request.args.get("search"):
        from_search = True

    person = get_person_info(wiki_id)
    top_entities_in_rel_type = get_top_relationships(wiki_id)  # ToDo: not being shown
    relationships_articles = get_person_relationships(wiki_id)

    # make titles with entities all clicklable
    for r in relationships_articles["opposes"]:
        make_title_linkable(r, wiki_id)

    for r in relationships_articles["supports"]:
        make_title_linkable(r, wiki_id)

    for r in relationships_articles["opposed_by"]:
        make_title_linkable(r, wiki_id)

    for r in relationships_articles["supported_by"]:
        make_title_linkable(r, wiki_id)

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
        "top_relations": top_entities_in_rel_type[:10],  # ToDo: not being shown
        "opposed": relationships_articles["opposes"],
        "supported": relationships_articles["supports"],
        "opposed_by": relationships_articles["opposed_by"],
        "supported_by": relationships_articles["supported_by"],
        "year_month_labels": year_month_labels,
        "opposed_freq": opposed_freq,
        "supported_freq": supported_freq,
        "opposed_by_freq": opposed_by_freq,
        "supported_by_freq": supported_by_freq,
    }

    if from_search:
        return render_template("entity_search.html", items=items)

    return render_template("entity.html", items=items)


@app.route("/party_members")
def party_members():
    global cached_members_parties
    wiki_id = request.args.get("q")

    if not cached_members_parties[wiki_id]:
        persons, party_name, party_logo = get_persons_affiliated_with_party(wiki_id)
        cached_members_parties[wiki_id] = persons
        cached_party_name[wiki_id] = party_name
        cached_party_logo[wiki_id] = party_logo
    else:
        persons = cached_members_parties[wiki_id]
        party_name = cached_party_name[wiki_id]
        party_logo = cached_party_logo[wiki_id]

    return render_template("party_members.html", items=persons, name=party_name, logo=party_logo)


@app.route("/parties")
def all_parties():
    global cached_all_parties

    if not cached_all_parties:
        items = get_all_parties()
        cached_all_parties = items
    else:
        items = cached_all_parties

    return render_template("all_parties.html", items=items)


@app.route("/person_party")
def get_person_party():
    person_wiki_id = request.args.get("entity")
    parties = get_party_of_entity(person_wiki_id)

    if not parties:
        return "None"

    # ToDo: handle the case with several parties/other things
    return jsonify(parties[0])


@app.route("/complete")
def complete():
    result = get_entities_without_image()
    return render_template("incomplete_entities.html", items=result)


@app.route("/queries")
def queries():

    print(request.args)
    query_nr = request.args.get("query_nr")

    if query_nr == "one":
        person_wiki_id = request.args.get("entity")
        party_wiki_id = request.args.get("party")
        # ToDo: pass name of person and party name to template
        results = get_list_of_persons_from_some_party_opposing_someone(
            person_wiki_id, party_wiki_id
        )
        return render_template("template_one.html", items=results)

    if query_nr == "two":
        person_wiki_id = request.args.get("entity")
        party_wiki_id = request.args.get("party")
        relationship = request.args.get("relationship")

        if relationship == "opoe-se":
            rel = "ent1_opposes_ent2"
        elif relationship == "apoia":
            rel = "ent1_supports_ent2"

        results = get_list_of_persons_from_some_party_relation_with_someone(
            person_wiki_id, party_wiki_id, rel
        )

        return render_template("template_one.html", items=results)
