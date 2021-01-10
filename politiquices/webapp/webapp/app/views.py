import json
import logging

from app import app
from flask import request, jsonify
from flask import render_template

from politiquices.webapp.webapp.app.data_models import Person
from politiquices.webapp.webapp.app.sparql_queries import (
    get_entities_without_image,
    get_nr_articles_per_year,
    get_nr_of_persons,
    get_party_of_entity,
    get_person_info,
    get_person_relationships,
    get_relationships_between_two_entities,
    get_top_relationships,
    get_total_nr_of_articles,
    get_wiki_id_affiliated_with_party,
    list_of_spec_relations_between_a_person_and_members_of_a_party,
    list_of_spec_relations_between_members_of_a_party_with_someone,
    list_of_spec_relations_between_two_parties,
)

from politiquices.webapp.webapp.app.relationships import build_relationships_freq

# ToDo: review have proper logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

person_no_image = "/static/images/no_picture.jpg"

with open("webapp/app/static/json/all_entities_info.json") as f_in:
    all_entities_info = json.load(f_in)

with open("webapp/app/static/json/all_parties_info.json") as f_in:
    all_parties_info = json.load(f_in)

with open("webapp/app/static/json/party_members.json") as f_in:
    all_parties_members = json.load(f_in)


entities_batch_size = 16


# Landing Page
@app.route("/")
def index():
    return render_template("index.html")


# Personalidades (first call)
@app.route("/entities")
def list_entities():
    return render_template("all_entities.html", items=all_entities_info[0:entities_batch_size])


# Personalidades (AJAX calls after first call)
@app.route("/load_entities")
def load_entities():
    start = int(request.args.get("last_index"))
    end = start + entities_batch_size
    print(start, end)
    return jsonify(all_entities_info[start:end])


# Personalidade View: called from 'Personalidade'-nav-bar or 'Personalidades'-click
@app.route("/entity")
def detail_entity():

    from_search = False
    wiki_id = request.args.get("q")
    if request.args.get("search"):
        from_search = True

    person = get_person_info(wiki_id)
    top_entities_in_rel_type = get_top_relationships(wiki_id)
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

    for r in relationships_articles["other"]:
        make_title_linkable(r, wiki_id)

    for r in relationships_articles["other_by"]:
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
        "positions": person.positions,
        "occupations": person.occupations,
        "education": person.education,
        "top_relations": top_entities_in_rel_type,
        "opposed": relationships_articles["opposes"],
        "supported": relationships_articles["supports"],
        "opposed_by": relationships_articles["opposed_by"],
        "supported_by": relationships_articles["supported_by"],
        "other": relationships_articles["other"],
        "other_by": relationships_articles["other_by"],
        "year_month_labels": year_month_labels,
        "opposed_freq": opposed_freq,
        "supported_freq": supported_freq,
        "opposed_by_freq": opposed_by_freq,
        "supported_by_freq": supported_by_freq,
    }

    if "annotate" in request.args:
        return render_template("entity_annotate.html", items=items)

    all_relationships_json = []

    opposed_json = []
    for i in items["opposed"]:
        # title with entities clickable and icon with link to arquivo.pt
        html_title = f"""
            {i['title_clickable']} <a id="link" href={i['url']} target="_blank">
            <img src="{i['link_image']}" width="{i['image_width']}" height="20"></a>
            """
        opposed_json.append({"data": i["date"], "titulo": html_title})
        all_relationships_json.append({"data": i["date"], "titulo": html_title})

    supported_json = []
    for i in items["supported"]:
        # title with entities clickable and icon with link to arquivo.pt
        html_title = f"""
            {i['title_clickable']} <a id="link" href={i['url']} target="_blank">
            <img src="{i['link_image']}" width="{i['image_width']}" height="20"></a>
            """
        supported_json.append({"data": i["date"], "titulo": html_title})
        all_relationships_json.append({"data": i["date"], "titulo": html_title})

    opposed_by_json = []
    for i in items["opposed_by"]:
        # title with entities clickable and icon with link to arquivo.pt
        html_title = f"""
            {i['title_clickable']} <a id="link" href={i['url']} target="_blank">
            <img src="{i['link_image']}" width="{i['image_width']}" height="20"></a>
            """
        opposed_by_json.append({"data": i["date"], "titulo": html_title})
        all_relationships_json.append({"data": i["date"], "titulo": html_title})

    supported_by_json = []
    for i in items["supported_by"]:
        # title with entities clickable and icon with link to arquivo.pt
        html_title = f"""
            {i['title_clickable']} <a id="link" href={i['url']} target="_blank">
            <img src="{i['link_image']}" width="{i['image_width']}" height="20"></a>
            """
        supported_by_json.append({"data": i["date"], "titulo": html_title})
        all_relationships_json.append({"data": i["date"], "titulo": html_title})

    for i in items["other"] + items["other_by"]:
        # title with entities clickable and icon with link to arquivo.pt
        html_title = f"""
            {i['title_clickable']} <a id="link" href={i['url']} target="_blank">
            <img src="{i['link_image']}" width="{i['image_width']}" height="20"></a>
            """
        all_relationships_json.append({"data": i["date"], "titulo": html_title})

    if from_search:
        return render_template(
            "entity_timeline.html",
            items=items,
            opposed=opposed_json,
            supported=supported_json,
            opposed_by=opposed_by_json,
            supported_by=supported_by_json,
            all_relationships=all_relationships_json,
        )

    return render_template(
        "entity.html",
        items=items,
        opposed=opposed_json,
        supported=supported_json,
        opposed_by=opposed_by_json,
        supported_by=supported_by_json,
        all_relationships=all_relationships_json,
    )


# Procurar
@app.route("/search")
def search():
    return render_template("search.html")


# Estatísticas
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


# Sobre
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/party_members")
def party_members():
    wiki_id = request.args.get("q")

    # get party info
    for x in all_parties_info:
        if x["wiki_id"] == wiki_id:
            party_name = x["party_label"]
            party_logo = x["party_logo"]

    # get all members
    persons = []
    members_id = all_parties_members[wiki_id]
    for member_id in members_id:
        for entity in all_entities_info:
            if member_id == entity["wikidata_id"]:
                persons.append(
                    Person(
                        name=entity["name"],
                        wiki_id=entity["wikidata_id"],
                        image_url=entity["image_url"],
                    )
                )

    return render_template(
        "party_members.html", items=persons, name=party_name, logo=party_logo, party_wiki_id=wiki_id
    )


@app.route("/parties")
def all_parties():
    return render_template("all_parties.html", items=all_parties_info)


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


def make_title_linkable(r, wiki_id):

    # add link to focus entity
    link_one = r["title"].replace(
        r["focus_ent"], '<a id="ent_1" href="entity?q=' + wiki_id + '">' + r["focus_ent"] + "</a>"
    )
    # add link to other entity page
    title_link = link_one.replace(
        r["other_ent_name"],
        '<a id="ent_2" href=' + r["other_ent_url"] + ">" + r["other_ent_name"] + "</a>",
    )
    r["title_clickable"] = title_link

    if r["url"].startswith("http://publico.pt"):
        r["link_image"] = "/static/images/114px-Logo_publico.png"
        r["image_width"] = "20"
    else:
        r["link_image"] = "/static/images/color_vertical.svg"
        r["image_width"] = "39.8"


def make_title_linkable_2_entities(r):

    ent1_wikid_id = r["ent1"].split("/")[-1]
    link_one = r["title"].replace(
        r["ent1_str"],
        '<a id="ent_1" href="entity?q=' + ent1_wikid_id + '">' + r["ent1_str"] + "</a>",
    )

    ent2_wikid_id = r["ent2"].split("/")[-1]
    title_link = link_one.replace(
        r["ent2_str"],
        '<a id="ent_2" href="entity?q=' + ent2_wikid_id + '">' + r["ent2_str"] + "</a>",
    )

    r["title_clickable"] = title_link

    if r["url"].startswith("http://publico.pt"):
        r["link_image"] = "/static/images/114px-Logo_publico.png"
        r["image_width"] = "20"

    else:
        r["link_image"] = "/static/images/color_vertical.svg"
        r["image_width"] = "39.8"


@app.route("/queries")
def queries():

    print(request.args)
    query_nr = request.args.get("query_nr")

    # relationships between two persons
    if query_nr == "two":
        person_one = request.args.get("e1")
        person_two = request.args.get("e2")

        person_one_info = get_person_info(person_one)
        person_two_info = get_person_info(person_two)
        results = get_relationships_between_two_entities(person_one, person_two)

        for r in results:
            make_title_linkable_2_entities(r)

        return render_template(
            "two_entities_relationships.html",
            items=results,
            entity_one=person_one_info,
            entity_two=person_two_info,
        )

    # relationships between (members of) a party and an entity
    if query_nr == "three":
        party_wiki_id = request.args.get("party")
        person_wiki_id = request.args.get("entity")
        relationship = request.args.get("relationship")

        if relationship == "opoe-se":
            rel = "ent1_opposes_ent2"
        elif relationship == "apoia":
            rel = "ent1_supports_ent2"

        results = list_of_spec_relations_between_members_of_a_party_with_someone(
            party_wiki_id, person_wiki_id, rel
        )

        for r in results:
            make_title_linkable_2_entities(r)

        return render_template("retrieved_relationships.html", items=results)

    # relationships between an entity and (members of) a party
    if query_nr == "four":
        person_wiki_id = request.args.get("entity")
        party_wiki_id = request.args.get("party")
        relationship = request.args.get("relationship")

        if relationship == "opoe-se":
            rel = "ent1_opposes_ent2"
        elif relationship == "apoia":
            rel = "ent1_supports_ent2"

        results = list_of_spec_relations_between_a_person_and_members_of_a_party(
            person_wiki_id, party_wiki_id, rel
        )

        for r in results:
            make_title_linkable_2_entities(r)
        return render_template("retrieved_relationships.html", items=results)

    # relationships between (members of) a party and (members of) another party
    if query_nr == "five":
        party_a = request.args.get("party_a")
        party_b = request.args.get("party_b")
        party_a = " ".join(["wd:" + x for x in get_wiki_id_affiliated_with_party(party_a)])
        party_b = " ".join(["wd:" + x for x in get_wiki_id_affiliated_with_party(party_b)])

        relationship = request.args.get("relationship")
        if relationship == "opoe-se":
            rel = "ent1_opposes_ent2"
        elif relationship == "apoia":
            rel = "ent1_supports_ent2"

        results = list_of_spec_relations_between_two_parties(party_a, party_b, rel)

        for r in results:
            make_title_linkable_2_entities(r)

        return render_template("retrieved_relationships.html", items=results)
