import json
import logging

from app import app
from flask import request, jsonify
from flask import render_template

from politiquices.webapp.webapp.app.sparql_queries import build_relationships_by_year, \
    list_of_spec_relations_between_two_persons
from politiquices.webapp.webapp.app.data_models import Person
from politiquices.webapp.webapp.app.sparql_queries import (
    get_entities_without_image,
    get_nr_articles_per_year,
    get_nr_of_persons,
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
from politiquices.webapp.webapp.app.utils import (
    clickable_title,
    make_json,
    get_relationship,
    per_vs_person_linkable
)

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
    titles_rels = get_person_relationships(wiki_id)

    # get the data to create the graph
    chart_js_data = build_relationships_by_year(wiki_id)

    # create a clickable title
    opposes = [clickable_title(r, wiki_id) for r in titles_rels["opposes"]]
    supports = [clickable_title(r, wiki_id) for r in titles_rels["supports"]]
    opposed_by = [clickable_title(r, wiki_id) for r in titles_rels["opposed_by"]]
    supported_by = [clickable_title(r, wiki_id) for r in titles_rels["supported_by"]]

    # only to be used in annotation mode
    other = [clickable_title(r, wiki_id) for r in titles_rels["other"]]
    other_by = [clickable_title(r, wiki_id) for r in titles_rels["other_by"]]

    opposed_json = make_json(opposes)
    supported_json = make_json(supports)
    opposed_by_json = make_json(opposed_by)
    supported_by_json = make_json(supported_by)
    all_relationships_json = opposed_json + supported_by_json + opposed_by_json + supported_by_json

    items = {
        # person information
        "wiki_id": person.wiki_id,
        "name": person.name,
        "image": person.image_url,
        "parties": person.parties,
        "positions": person.positions,
        "occupations": person.occupations,
        "education": person.education,
        # titles/articles frequency by relationships by year, for ChartJS
        "year_month_labels": chart_js_data["labels"],
        "opposed_freq": chart_js_data["opposed_freq"],
        "supported_freq": chart_js_data["supported_freq"],
        "opposed_by_freq": chart_js_data["opposed_by_freq"],
        "supported_by_freq": chart_js_data["supported_by_freq"],
        # top-persons in each relationship
        "top_relations": top_entities_in_rel_type,
    }

    # show a different interface allowing to annotate/correct relationships
    if "annotate" in request.args:
        items.update(
            {
                "opposes": opposes,
                "supports": supports,
                "opposed_by": opposed_by,
                "supported_by": supported_by,
                "other": other,
                "other_by": other_by,
            }
        )
        return render_template("entity_annotate.html", items=items)

    if from_search:
        return render_template(
            "entity_info.html",
            # common info from above goes in 'items', i.e.: person info, chart, top-relations
            items=items,
            # JSONs for the tables
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
            if member_id == entity["wiki_id"]:
                persons.append(
                    Person(
                        name=entity["name"],
                        nr_articles=int(entity["nr_articles"]),
                        wiki_id=entity["wiki_id"],
                        image_url=entity["image_url"],
                    )
                )

    sorted_persons = sorted(persons, key=lambda x: x.nr_articles, reverse=True)
    return render_template(
        "party_members.html",
        items=sorted_persons,
        name=party_name,
        logo=party_logo,
        party_wiki_id=wiki_id,
    )


# Grafo
@app.route("/graph")
def graph():
    return render_template("graph.html")


# Grafo
@app.route("/graph_all")
def graph_all():
    return render_template("graph_all.html")


# Estatísticas
@app.route("/stats")
def status():
    # single values
    nr_persons = get_nr_of_persons()
    nr_parties = len(all_parties_info)

    # articles per year chart
    nr_articles_year_labels, nr_articles_year_values = get_nr_articles_per_year()
    nr_articles = get_total_nr_of_articles()

    # personality frequency chart
    per_freq_labels = []
    per_freq_values = []
    per_freq = all_persons_freq()
    for x in per_freq:
        per_freq_labels.append(wiki_id_info[x["person"].split("/")[-1]]["name"])
        per_freq_values.append(x["freq"])

    # person co-occurrence chart
    co_occurrences_labels = []
    co_occurrences_values = []
    with open("webapp/app/static/json/top_co_occurrences.json") as f_in:
        top_co_occurrences = json.load(f_in)
    for x in top_co_occurrences:
        co_occurrences_labels.append(x["person_a"]["name"] + " / " + x["person_b"]["name"])
        co_occurrences_values.append(x["nr_occurrences"])

    items = {
        "nr_parties": nr_parties,
        "nr_persons": nr_persons,
        "nr_articles": nr_articles,
        "nr_articles_year_labels": nr_articles_year_labels,
        "nr_articles_year_values": nr_articles_year_values,
        "per_freq_labels": per_freq_labels,
        "per_freq_values": per_freq_values,
        "per_co_occurrence_labels": co_occurrences_labels,
        "per_co_occurrence_values": co_occurrences_values,
    }

    return render_template("stats.html", items=items)


# Sobre
@app.route("/about")
def about():
    return render_template("about.html")


# other: personalities without image
@app.route("/complete")
def complete():
    result = get_entities_without_image()
    return render_template("incomplete_entities.html", items=result)


def get_info(wiki_id):
    if info := [entry for entry in all_parties_info if entry["wiki_id"] == wiki_id]:
        return info[0], "party"

    if info := [entry for entry in all_entities_info if entry["wiki_id"] == wiki_id]:
        return info[0], "person"


def entity_vs_entity(person_one, person_two):
    """
    get all the relationships between two persons
    """
    person_one_info = get_person_info(person_one)
    person_two_info = get_person_info(person_two)
    results, rels_freq_by_year = get_relationships_between_two_entities(person_one, person_two)

    for r in results:
        per_vs_person_linkable(r)

    opposed = make_json([r for r in results if r['rel_type_new'] == 'ent1_opposes_ent2'])
    supported = make_json([r for r in results if r['rel_type_new'] == 'ent1_supports_ent2'])
    opposed_by = make_json([r for r in results if r['rel_type_new'] == 'ent1_opposed_by_ent2'])
    supported_by = make_json([r for r in results if r['rel_type_new'] == 'ent1_supported_by_ent2'])
    all_json = opposed + supported + opposed_by + supported_by

    # build chart information
    labels = list(rels_freq_by_year.keys())
    ent1_opposes_ent2 = []
    ent1_supports_ent2 = []
    ent1_opposed_by_ent2 = []
    ent1_supported_by_ent2 = []
    for year in rels_freq_by_year:
        ent1_opposes_ent2.append(rels_freq_by_year[year]["ent1_opposes_ent2"])
        ent1_supports_ent2.append(rels_freq_by_year[year]["ent1_supports_ent2"])
        ent1_opposed_by_ent2.append(rels_freq_by_year[year]["ent1_opposed_by_ent2"])
        ent1_supported_by_ent2.append(rels_freq_by_year[year]["ent1_supported_by_ent2"])

    return render_template(
        "entity_vs_entity.html",
        # title relationships
        opposed=opposed,
        supported=supported,
        opposed_by=opposed_by,
        supported_by=supported_by,
        all_relationships=all_json,
        # persons information
        entity_one=person_one_info,
        entity_two=person_two_info,
        # chart information
        labels=labels,
        ent1_opposes_ent2=ent1_opposes_ent2,
        ent1_supports_ent2=ent1_supports_ent2,
        ent1_opposed_by_ent2=ent1_opposed_by_ent2,
        ent1_supported_by_ent2=ent1_supported_by_ent2,
    )


def person_vs_person_restricted(person_one, person_two, rel_text, person_one_info, person_two_info):
    rel = get_relationship(rel_text)
    results = list_of_spec_relations_between_two_persons(person_one, person_two, rel)
    for r in results:
        per_vs_person_linkable(r)
    relationships_json = make_json([r for r in results if r['rel_type'] == rel])
    return render_template(
        "query_person_person.html",
        relationship_text=rel_text,
        relationships=relationships_json,
        person_one=person_one_info,
        person_two=person_two_info,
    )


def party_vs_person(party_wiki_id, person_wiki_id, rel_text, party_info, person_info):
    """
    relationships between (members of) a party and an entity
    """
    rel = get_relationship(rel_text)
    results = list_of_spec_relations_between_members_of_a_party_with_someone(
        party_wiki_id, person_wiki_id, rel
    )
    for r in results:
        per_vs_person_linkable(r)
    person_info = get_person_info(person_wiki_id)
    relationships_json = make_json([r for r in results if r['rel_type'] == rel])
    return render_template(
        "query_party_person.html",
        relationship_text=rel_text,
        relationships=relationships_json,
        party=party_info,
        person=person_info,
    )


def person_vs_party(person_wiki_id, party_wiki_id, rel_text, person_info, party_info):
    """
    relationships between an entity and (members of) a party
    """
    rel = get_relationship(rel_text)
    results = list_of_spec_relations_between_a_person_and_members_of_a_party(
        person_wiki_id, party_wiki_id, rel
    )
    for r in results:
        per_vs_person_linkable(r)
    person_info = get_person_info(person_wiki_id)
    relationships_json = make_json([r for r in results if r['rel_type'] == rel])
    return render_template(
        "query_person_party.html",
        relationship_text=rel_text,
        relationships=relationships_json,
        person=person_info,
        party=party_info,
    )


def party_vs_party(party_a, party_b, rel_text, party_a_info, party_b_info):
    """
    relationships between (members of) a party and (members of) another party
    """
    party_a_members = " ".join(["wd:" + x for x in get_wiki_id_affiliated_with_party(party_a)])
    party_b_members = " ".join(["wd:" + x for x in get_wiki_id_affiliated_with_party(party_b)])

    rel = get_relationship(rel_text)

    results = list_of_spec_relations_between_two_parties(party_a_members, party_b_members, rel)

    for r in results:
        per_vs_person_linkable(r)

    relationships_json = make_json([r for r in results if r['rel_type'] == rel])

    return render_template(
        "query_party_party.html",
        relationship_text=rel_text,
        relationships=relationships_json,
        party_one=party_a_info,
        party_two=party_b_info,
    )


@app.route("/queries")
def queries():
    print(request.args)
    query_nr = request.args.get("query_nr")

    if query_nr == "two":
        entity_one = request.args.get("e1")
        entity_two = request.args.get("e2")
        return entity_vs_entity(entity_one, entity_two)

    if query_nr == "one":
        entity_one = request.args.get("e1")
        entity_two = request.args.get("e2")
        rel_text = request.args.get("relationship")
        e1_info, e1_type = get_info(entity_one)
        e2_info, e2_type = get_info(entity_two)

        if e1_type == "person" and e2_type == "person":
            return person_vs_person_restricted(entity_one, entity_two, rel_text, e1_info, e2_info)

        elif e1_type == "party" and e2_type == "person":
            return party_vs_person(entity_one, entity_two, rel_text, e1_info, e2_info)

        elif e1_type == "person" and e2_type == "party":
            return person_vs_party(entity_one, entity_two, rel_text, e1_info, e2_info)

        elif e1_type == "party" and e2_type == "party":
            return party_vs_party(entity_one, entity_two, rel_text, e1_info, e2_info)
