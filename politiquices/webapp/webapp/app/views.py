import json
import logging

from app import app
from flask import request, jsonify
from flask import render_template


from politiquices.webapp.webapp.app.sparql_queries import (
    get_entities_without_image,
    get_nr_articles_per_year,
    get_nr_of_persons,
    get_party_of_entity,
    get_person_info,
    get_person_relationships,
    get_persons_affiliated_with_party,
    get_relationships_between_two_entities,
    get_top_relationships,
    get_total_nr_of_articles,
    get_wiki_id_affiliated_with_party,
    list_of_spec_relations_between_a_person_and_members_of_a_party,
    list_of_spec_relations_between_members_of_a_party_with_someone,
    list_of_spec_relations_between_two_parties
)

from politiquices.webapp.webapp.app.relationships import build_relationships_freq

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

person_no_image = "/static/images/no_picture.jpg"

all_entities_info = None
all_parties_info = None


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


@app.route("/load_entities")
def load_entities():
    start = int(request.args.get("last_index"))
    end = start + 36
    print(start, end)
    return jsonify(all_entities_info[start:end])


@app.route("/entities")
def list_entities():
    global all_entities_info
    if not all_entities_info:
        with open("webapp/app/static/all_entities.json") as f_in:
            all_entities_info = json.load(f_in)
    return render_template("all_entities.html", items=all_entities_info[0:36])


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
        "offices": person.positions,
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

    if from_search:
        return render_template("entity_search.html", items=items)

    return render_template("entity.html", items=items)


@app.route("/party_members")
def party_members():
    wiki_id = request.args.get("q")
    persons, party_name, party_logo = get_persons_affiliated_with_party(wiki_id)
    return render_template("party_members.html", items=persons, name=party_name, logo=party_logo)


@app.route("/parties")
def all_parties():
    global all_parties_info
    if not all_parties_info:
        with open("webapp/app/static/all_parties_info.json") as f_in:
            all_parties_info = json.load(f_in)

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


def make_title_linkable_2_entities(r):

    ent1_wikid_id = r['ent1'].split("/")[-1]
    link_one = r['title'].replace(
        r['ent1_str'],
        '<a id="ent_1" href="entity?q=' + ent1_wikid_id + '">' + r['ent1_str'] + '</a>'
    )

    ent2_wikid_id = r['ent2'].split("/")[-1]
    title_link = link_one.replace(
        r['ent2_str'],
        '<a id="ent_2" href="entity?q=' + ent2_wikid_id + '">' + r['ent2_str'] + '</a>'
    )

    r['title_clickable'] = title_link

    if r['url'].startswith('http://publico.pt'):
        r['link_image'] = "/static/images/114px-Logo_publico.png"
        r['image_width'] = "20"

    else:
        r['link_image'] = "/static/images/color_vertical.svg"
        r['image_width'] = "39.8"


@app.route("/queries")
def queries():

    print(request.args)
    query_nr = request.args.get("query_nr")

    # relationships between two persons
    if query_nr == 'two':
        person_one = request.args.get("e1")
        person_two = request.args.get("e2")
        results = get_relationships_between_two_entities(person_one, person_two)
        for r in results:
            make_title_linkable_2_entities(r)
        return render_template("two_entities_relationships.html", items=results)

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
        return render_template("template_one.html", items=results)

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
        return render_template("template_one.html", items=results)

    # relationships between (members of) a party and (members of) another party
    if query_nr == "five":
        party_a = request.args.get("party_a")
        party_b = request.args.get("party_b")

        party_a = ' '.join(['wd:'+x for x in get_wiki_id_affiliated_with_party(party_a)])
        party_b = ' '.join(['wd:'+x for x in get_wiki_id_affiliated_with_party(party_b)])

        relationship = request.args.get("relationship")
        if relationship == "opoe-se":
            rel = "ent1_opposes_ent2"
        elif relationship == "apoia":
            rel = "ent1_supports_ent2"

        results = list_of_spec_relations_between_two_parties(party_a, party_b, rel)

        for r in results:
            make_title_linkable_2_entities(r)

        return render_template("two_entities_relationships.html", items=results)
