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
    all_persons_freq,
)

from politiquices.webapp.webapp.app.relationships import (
    build_relationships_year_month_freq,
    build_relationships_by_year,
)
from politiquices.webapp.webapp.app.utils import make_title_linkable
from politiquices.webapp.webapp.app.utils import make_title_linkable_2_entities

# ToDo: review have proper logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

person_no_image = "/static/images/no_picture.jpg"

# load all static generated caching stuff
with open("webapp/app/static/json/all_entities_info.json") as f_in:
    all_entities_info = json.load(f_in)

with open("webapp/app/static/json/all_parties_info.json") as f_in:
    all_parties_info = json.load(f_in)

with open("webapp/app/static/json/party_members.json") as f_in:
    all_parties_members = json.load(f_in)

with open("webapp/app/static/json/wiki_id_info.json") as f_in:
    wiki_id_info = json.load(f_in)

with open("webapp/app/static/json/edges.json") as f_in:
    edges = json.load(f_in)


entities_batch_size = 16


# Landing Page
@app.route("/")
def index():
    return render_template("index.html")


# Personalidades (first call)
@app.route("/entities")
def list_entities():
    return render_template("personalidades.html", items=all_entities_info[0:entities_batch_size])


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

    """
    (
        year_month_labels,
        opposed_freq,
        supported_freq,
        opposed_by_freq,
        supported_by_freq,
    ) = build_relationships_year_month_freq(wiki_id)
    """

    (
        all_years,
        opposed_freq,
        supported_freq,
        opposed_by_freq,
        supported_by_freq,
    ) = build_relationships_by_year(wiki_id)

    items = {
        # person information
        "wiki_id": person.wiki_id,
        "name": person.name,
        "image": person.image_url,
        "parties": person.parties,
        "positions": person.positions,
        "occupations": person.occupations,
        "education": person.education,

        # top-persons in each relationship
        "top_relations": top_entities_in_rel_type,

        # titles/articles supporting relationships
        "opposed": relationships_articles["opposes"],
        "supported": relationships_articles["supports"],
        "opposed_by": relationships_articles["opposed_by"],
        "supported_by": relationships_articles["supported_by"],
        "other": relationships_articles["other"],
        "other_by": relationships_articles["other_by"],

        # titles/articles frequency supporting relationships by year
        "year_month_labels": all_years,
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


# Partidos
@app.route("/parties")
def all_parties():
    return render_template("all_parties.html", items=all_parties_info)


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


@app.route("/person_party")
def get_person_party():
    person_wiki_id = request.args.get("entity")
    parties = get_party_of_entity(person_wiki_id)

    if not parties:
        return "None"

    # ToDo: handle the case with several parties/other things
    return jsonify(parties[0])


# Procurar
@app.route("/search")
def search():
    return render_template("search.html")


# Grafo
@app.route("/graph")
def graph():
    nodes = set()
    elements = []

    # ToDo: rever o quer SPARQL (apenas 548 personalidades? porque?)
    # ToDo: 'classes' no elemento para associar a um partido

    for x in edges:
        name_a = wiki_id_info[x["person_a"].split("/")[-1]]["name"]
        name_b = wiki_id_info[x["person_b"].split("/")[-1]]["name"]
        wiki_id_a = x["person_a"].split("/")[-1]
        wiki_id_b = x["person_b"].split("/")[-1]

        if wiki_id_a in nodes:
            continue
        else:
            elements.append({"data": {"id": wiki_id_a, "label": name_a}})
            nodes.add(name_a)

        if wiki_id_b in nodes:
            continue
        else:
            elements.append({"data": {"id": wiki_id_b, "label": name_b}})
            nodes.add(name_b)

        if x["rel_type"].startswith("ent1"):
            elements.append(
                {
                    "data": {
                        "id": x["url"],
                        "source": wiki_id_a,
                        "target": wiki_id_b,
                        "label": x["rel_type"],
                    }
                }
            )

        elif x["rel_type"].startswith("ent2"):
            elements.append(
                {
                    "data": {
                        "id": x["url"],
                        "source": wiki_id_b,
                        "target": wiki_id_a,
                        "label": x["rel_type"],
                    }
                }
            )

    return render_template("graph.html", elements=elements[:100])


# Estatísticas
@app.route("/stats")
def status():

    # ToDo: nr. parties
    # ToDo: make links
    # ToDo: refactor/normalize this code for all values/graphs

    year, nr_articles_year = get_nr_articles_per_year()
    nr_persons = get_nr_of_persons()
    nr_articles = get_total_nr_of_articles()
    per_freq = all_persons_freq()
    items = {
        "nr_persons": nr_persons,
        "nr_articles": nr_articles,
        "year_labels": year,
        "year_articles": nr_articles_year,
    }

    labels = [wiki_id_info[x["person"].split("/")[-1]]["name"] for x in per_freq]
    values = [x["freq"] for x in per_freq]
    return render_template(
        "stats.html", items=items, per_freq_labels=labels, per_freq_values=values
    )


# Sobre
@app.route("/about")
def about():
    return render_template("about.html")


# other: personalities without image
@app.route("/complete")
def complete():
    result = get_entities_without_image()
    return render_template("incomplete_entities.html", items=result)


# handling input from Procurar and front-page queries
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
            "query_person_person.html",
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

        # ToDo: this can be improved, e.g.: make a mapping after loading the json
        party_info = [entry for entry in all_parties_info if entry["wiki_id"] == party_wiki_id][0]
        person_info = get_person_info(person_wiki_id)

        return render_template(
            "query_party_person.html", items=results, party=party_info, person=person_info,
        )

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

        # ToDo: this can be improved, e.g.: make a mapping after loading the json
        party_info = [entry for entry in all_parties_info if entry["wiki_id"] == party_wiki_id][0]
        person_info = get_person_info(person_wiki_id)

        return render_template(
            "query_person_party.html", items=results, party=party_info, person=person_info,
        )

    # relationships between (members of) a party and (members of) another party
    if query_nr == "five":
        party_a = request.args.get("party_a")
        party_b = request.args.get("party_b")
        party_a_members = " ".join(["wd:" + x for x in get_wiki_id_affiliated_with_party(party_a)])
        party_b_members = " ".join(["wd:" + x for x in get_wiki_id_affiliated_with_party(party_b)])

        relationship = request.args.get("relationship")
        if relationship == "opoe-se":
            rel = "ent1_opposes_ent2"
        elif relationship == "apoia":
            rel = "ent1_supports_ent2"

        results = list_of_spec_relations_between_two_parties(party_a_members, party_b_members, rel)

        for r in results:
            make_title_linkable_2_entities(r)

        # ToDo: this can be improved, e.g.: make a mapping after loading the json
        party_one_info = [entry for entry in all_parties_info if entry["wiki_id"] == party_a][0]
        party_two_info = [entry for entry in all_parties_info if entry["wiki_id"] == party_b][0]

        return render_template(
            "query_party_party.html",
            items=results,
            party_one=party_one_info,
            party_two=party_two_info,
        )
