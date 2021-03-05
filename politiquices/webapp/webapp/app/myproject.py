import json

from flask import Flask
from flask import request, jsonify
from flask import render_template

from politiquices.webapp.webapp.lib.utils import get_info
from politiquices.webapp.webapp.config import entities_batch_size
from politiquices.webapp.webapp.lib.cache import (
    all_entities_info,
    all_parties_info,
    all_parties_members,
    chave_publico,
    wiki_id_info,
)

from politiquices.webapp.webapp.lib.data_models import Person
from politiquices.webapp.webapp.lib.graph import get_entity_network, get_network
from politiquices.webapp.webapp.lib.render_queries import (
    party_vs_party,
    person_vs_party,
    party_vs_person,
    person_vs_person,
    entity_vs_entity,
    entity_full_story
)

from politiquices.webapp.webapp.lib.sparql_queries import (
    get_entities_without_image,
    get_nr_articles_per_year,
    get_nr_of_persons,
    get_persons_articles_freq,
    get_relationships_to_annotate,
    get_total_articles_by_year_by_relationship_type,
    get_total_nr_of_articles,
)


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


# Personalidades (first call)
@app.route("/entities")
def list_entities():
    return render_template("personalidades.html", items=all_entities_info[0:entities_batch_size])


# handles 'Personalidades' scroll down, response to AJAX calls
@app.route("/load_entities")
def load_entities():
    start = int(request.args.get("last_index"))
    end = start + entities_batch_size
    return jsonify(all_entities_info[start:end])


# Personalidade View: called from 'Personalidade'-nav-bar or 'Personalidades'-click
@app.route("/entity")
def detail_entity():
    # get args
    from_search = True if request.args.get("search") else False
    annotate = True if request.args.get("annotate") else False
    wiki_id = request.args.get("q")

    # get data
    data = entity_full_story(wiki_id, annotate)

    # render an annotation template
    if annotate:
        return render_template("entity_annotate.html", items=data)

    # decide which template to use
    template = "entity_info.html" if from_search else "entity.html"

    return render_template(
        template,
        items=data,
        opposed=data['opposed'],
        supported=data['supported'],
        opposed_by=data['opposed_by'],
        supported_by=data['supported_by'],
        all_relationships=data['all_relationships']
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


@app.route("/stats")
def status():
    from datetime import datetime
    print(datetime.now())

    # number of persons, parties
    nr_persons = get_nr_of_persons()
    nr_parties = len(all_parties_info)

    # articles per year chart
    nr_articles_year_labels, nr_articles_year_values = get_nr_articles_per_year()
    nr_articles = get_total_nr_of_articles()

    # articles per relationship type per year chart
    values = get_total_articles_by_year_by_relationship_type()

    # personality frequency chart
    per_freq_labels = []
    per_freq_values = []
    per_freq = get_persons_articles_freq()
    for x in per_freq:
        per_freq_labels.append(wiki_id_info[x["person"].split("/")[-1]]["name"])
        per_freq_values.append(x["freq"])

    # person co-occurrence chart
    co_occurrences_labels = []
    co_occurrences_values = []
    with open("static/json/top_co_occurrences.json") as f_in:
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

        "ent1_opposes_ent2": [values[year]['ent1_opposes_ent2'] for year in values],
        "ent2_opposes_ent1": [values[year]['ent2_opposes_ent1'] for year in values],
        "ent1_supports_ent2": [values[year]['ent1_supports_ent2'] for year in values],
        "ent2_supports_ent1": [values[year]['ent2_supports_ent1'] for year in values],
        "ent1_other_ent2": [values[year]['ent1_other_ent2'] for year in values],
        "ent2_other_ent1": [values[year]['ent2_other_ent1'] for year in values],

        "per_freq_labels": per_freq_labels[0:500],
        "per_freq_values": per_freq_values[0:500],

        "per_co_occurrence_labels": co_occurrences_labels[0:75],
        "per_co_occurrence_values": co_occurrences_values[0:75],
    }

    return render_template("stats.html", items=items)


@app.route("/about")
def about():
    return render_template("about.html")


# other: personalities without image
@app.route("/complete")
def complete():
    result = get_entities_without_image()
    return render_template("incomplete_entities.html", items=result)


# to render documents from the CHAVE collection
@app.route("/chave")
def chave():
    chave_id = request.args.get("q")
    article = [article for article in chave_publico if article["id"] == chave_id][0]
    article["text"] = article["text"].replace("\n", "<br><br>")
    return render_template("chave_template.html", article=article)


@app.route("/annotate")
def annotations():
    to_annotate = get_relationships_to_annotate()

    for idx, r in enumerate(to_annotate):
        link_one = r["title"].replace(
            r["ent1_str"],
            '<a id="ent_1" href="entity?q='
            + r["ent1"].split("/")[-1]
            + '">'
            + r["ent1_str"]
            + "</a>",
        )

        title_link = link_one.replace(
            r["ent2_str"],
            '<a id="ent_2" href="entity?q='
            + r["ent2"].split("/")[-1]
            + '">'
            + r["ent2_str"]
            + "</a>",
        )

        r["title_clickable"] = title_link
        r["id"] = idx

    return render_template("annotate_other.html", items=to_annotate)


@app.route("/graph")
def graph():
    relation = "ACUSA|APOIA"
    year_from = "2000"
    year_to = "2019"
    freq_min = 10
    freq_max = 30
    k_clique = 3
    entity = None

    # if not arguments were given, render graph with default arguments
    if not list(request.args.items()):
        nodes, edges = get_network(relation, year_from, year_to, freq_max, freq_min, k_clique)
        return render_template("graph.html", nodes=nodes, edges=edges)

    freq_min = int(request.args.get("freq_min"))
    freq_max = int(request.args.get("freq_max"))
    rel_type = request.args.get("rel_type")
    if rel_type == "supports":
        relation = "APOIA"
    elif rel_type == "opposes":
        relation = "ACUSA"
    else:
        relation = "ACUSA|APOIA"

    k_clique = int(request.args.get("k_clique"))
    year_from = request.args.get("year_from")
    year_to = request.args.get("year_to")

    # get the network of a specific person
    if wiki_id := request.args.get('entity'):
        nodes, edges = get_entity_network(wiki_id, relation, freq_min, freq_max, year_from, year_to)
        return jsonify({"nodes": nodes, "edges": edges})

    nodes, edges = get_network(relation, year_from, year_to, freq_max, freq_min, k_clique)
    return jsonify({"nodes": nodes, "edges": edges})


@app.route("/queries")
def queries():
    print(request.args)
    query_nr = request.args.get("query_nr")

    if query_nr == "two":
        entity_one = request.args.get("e1")
        entity_two = request.args.get("e2")
        data = entity_vs_entity(entity_one, entity_two)
        if data is None:
            return render_template("no_results.html")
        return render_template(
            "entity_vs_entity.html",

            # title relationships
            opposed=data['opposed'],
            supported=data['supported'],
            opposed_by=data['opposed_by'],
            supported_by=data['supported_by'],
            # ToDo: duplicate from above...very ugly
            all_relationships=data['all_relationships'],

            # persons information
            entity_one=data['person_one_info'],
            entity_two=data['person_two_info'],

            # chart information
            labels=data['labels'],
            ent1_opposes_ent2=data['ent1_opposes_ent2'],
            ent1_supports_ent2=data['ent1_supports_ent2'],
            ent1_opposed_by_ent2=data['ent1_opposed_by_ent2'],
            ent1_supported_by_ent2=data['ent1_supported_by_ent2']
        )

    if query_nr == "one":
        html = False
        annotate = False

        # NOTE: this is all very very hacky...scary!
        year_from = request.args.get("year_from")
        year_to = request.args.get("year_to")
        year = request.args.get("year")
        if year and (not year_from and not year_to):
            year_from = year
            year_to = year

        if "html" in request.args:
            html = True

        if "annotate" in request.args:
            annotate = True

        entity_one = request.args.get("e1")
        entity_two = request.args.get("e2")
        rel_text = request.args.get("relationship")
        e1_info, e1_type = get_info(entity_one)
        e2_info, e2_type = get_info(entity_two)

        if e1_type == "person" and e2_type == "person":

            data = person_vs_person(entity_one, entity_two, rel_text, year_from, year_to, annotate)

            if data is None:
                return render_template("no_results.html")

            if annotate:
                return render_template(
                    "query_person_person_annotate.html",
                    entity_one=e1_info,
                    entity_two=e2_info,
                    items=data['items'],
                )

            if html:
                return render_template(
                    "query_person_person_full.html",
                    relationship_text=rel_text,
                    rel_text=rel_text,
                    relationships=data['relationships'],
                    person_one=e1_info,
                    person_two=e2_info,
                    labels=data['labels'],
                    rel_freq_year=data['rel_freq_year'],
                )

            return render_template(
                "query_person_person.html",
                relationship_text=rel_text,
                rel_text=rel_text,
                relationships=data['relationships'],
                person_one=e1_info,
                person_two=e2_info,
                labels=data['labels'],
                rel_freq_year=data['rel_freq_year'],
            )

        elif e1_type == "party" and e2_type == "person":
            data = party_vs_person(entity_one, entity_two, rel_text, year_from, year_to)
            if data is None:
                return render_template("no_results.html")
            return render_template(
                "query_party_person.html",
                relationship_text=rel_text,
                relationships=data['relationships_json'],
                party=e1_info,
                person=e2_info,
                labels=data['labels'],
                rel_freq_year=data['rel_freq_year'],
                rel_text=rel_text,
                heatmap=data['heatmap'],
                heatmap_gradient=data['heatmap_gradient'],
                heatmap_height=data['heatmap_height']
            )

        elif e1_type == "person" and e2_type == "party":
            data = person_vs_party(entity_one, entity_two, rel_text, year_from, year_to)
            if data is None:
                return render_template("no_results.html")
            return render_template(
                "query_person_party.html",
                relationship_text=rel_text,
                relationships=data['relationships_json'],
                person=e1_info,
                party=e2_info,
                labels=data['labels'],
                rel_freq_year=data['rel_freq_year'],
                rel_text=rel_text,
                heatmap=data['heatmap'],
                heatmap_gradient=data['heatmap_gradient'],
                heatmap_height=data['heatmap_height']
            )

        elif e1_type == "party" and e2_type == "party":
            data = party_vs_party(entity_one, entity_two, rel_text, year_from, year_to)
            if data is None:
                return render_template("no_results.html")
            return render_template(
                "query_party_party.html",
                relationship_text=rel_text,
                relationships=data['relationships_json'],
                party_one=e1_info,
                party_two=e2_info,
                labels=data['labels'],
                rel_freq_year=data['rel_freq_year'])


if __name__ == "__main__":
    app.run(host='0.0.0.0')
