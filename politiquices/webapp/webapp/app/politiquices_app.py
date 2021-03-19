from flask import Flask
from flask import request, jsonify, render_template

from politiquices.webapp.webapp.config import entities_batch_size
from politiquices.webapp.webapp.lib.utils import get_info
from politiquices.webapp.webapp.lib.graph import get_entity_network, get_network
from politiquices.webapp.webapp.lib.cache import all_entities_info, all_parties_info, chave_publico
from politiquices.webapp.webapp.lib.render_queries import (
    party_vs_party,
    person_vs_party,
    party_vs_person,
    person_vs_person,
    entity_vs_entity,
    entity_full_story,
    get_party_members,
    get_stats
)

from politiquices.webapp.webapp.lib.sparql_queries import (
    get_entities_without_image,
    get_relationships_to_annotate, personalities_only_with_other,
)


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


# Personalidades (first call)
@app.route("/entities")
def list_entities():
    return render_template("personalidades.html",
                           items=all_entities_info[0:entities_batch_size],
                           batch_size=entities_batch_size)


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
    print(request.args)
    from_search = True if 'search' in request.args else False
    annotate = True if 'annotate' in request.args else False
    wiki_id = request.args.get("q")

    # get data
    data = entity_full_story(wiki_id, annotate)

    # render an annotation template
    if annotate:
        return render_template("entity_annotate.html", items=data)

    # decide which template to use
    template = "entity_content.html" if from_search else "entity.html"

    return render_template(
        template,
        items=data,
        opposed=data['opposed'],
        supported=data['supported'],
        opposed_by=data['opposed_by'],
        supported_by=data['supported_by'],
        all_relationships=data['all_relationships']
    )


@app.route("/parties")
def all_parties():
    return render_template("all_parties.html", items=all_parties_info)


@app.route("/party_members")
def party_members():
    wiki_id = request.args.get("q")
    data = get_party_members(wiki_id)
    return render_template(
        "party_members.html",
        items=data['members'],
        name=data['party_name'],
        logo=data['party_logo'],
        party_wiki_id=wiki_id,
    )


@app.route("/stats")
def stats():
    data = get_stats()
    return render_template("stats.html", items=data)


@app.route("/graph")
def graph():
    relation = "ACUSA|APOIA"
    year_from = "2000"
    year_to = "2019"
    freq_min = 10
    freq_max = 30

    print(request.args)

    # if not arguments were given, render graph with default arguments
    if not list(request.args.items()):
        nodes, edges = get_network(relation, year_from, year_to, freq_max, freq_min, k_clique=3)
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

    year_from = request.args.get("year_from")
    year_to = request.args.get("year_to")

    # get the network of a specific person
    if wiki_id := request.args.get('entity'):
        nodes, edges = get_entity_network(wiki_id, relation, freq_min, freq_max, year_from, year_to)
        return jsonify({"nodes": nodes, "edges": edges})

    nodes, edges = get_network(relation, year_from, year_to, freq_max, freq_min, k_clique=3)
    return jsonify({"nodes": nodes, "edges": edges})


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/versus")
def entity_versus_entity():
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


@app.route("/queries")
def queries():
    print(request.args)
    # entity and relationship args
    entity_one = request.args.get("e1")
    entity_two = request.args.get("e2")

    if not entity_one or not entity_two:
        return render_template("index.html")

    # which type of rendering ?
    annotate = True if "annotate" in request.args else False

    # time interval for the query
    year_from = request.args.get("year_from")
    year_to = request.args.get("year_to")
    year = request.args.get("year")
    if year and (not year_from and not year_to):
        year_from = year
        year_to = year

    rel_type = request.args.get("relationship")
    e1_info, e1_type = get_info(entity_one, all_entities_info, all_parties_info)
    e2_info, e2_type = get_info(entity_two, all_entities_info, all_parties_info)

    if e1_type == "person" and e2_type == "person":
        data = person_vs_person(entity_one, entity_two, rel_type, year_from, year_to, annotate)

        if data is None:
            return render_template("no_results.html")

        if annotate:
            return render_template(
                "query_person_person_annotate.html",
                entity_one=e1_info,
                entity_two=e2_info,
                items=data['items'],
            )

        return render_template(
            "query_person_person.html",
            relationship_text=data['relationship_text'],
            relationship_color=data['relationship_color'],
            relationships=data['relationships'],
            person_one=e1_info,
            person_two=e2_info,
            labels=data['labels'],
            rel_freq_year=data['rel_freq_year'],
        )

    elif e1_type == "party" and e2_type == "person":
        data = party_vs_person(entity_one, entity_two, rel_type, year_from, year_to)

        if data is None:
            return render_template("no_results.html")

        return render_template(
            "query_party_person.html",
            party=e1_info,
            person=e2_info,
            relationships=data['relationships_json'],
            relationship_text=data['relationship_text'],
            labels=data['labels'],
            rel_freq_year=data['rel_freq_year'],
            rel_type=rel_type,
            heatmap=data['heatmap'],
            heatmap_height=data['heatmap_height'],
            relationship_color=data['relationship_color']
        )

    elif e1_type == "person" and e2_type == "party":
        data = person_vs_party(entity_one, entity_two, rel_type, year_from, year_to)

        if data is None:
            return render_template("no_results.html")

        return render_template(
            "query_person_party.html",
            person=e1_info,
            party=e2_info,
            relationships=data['relationships_json'],
            relationship_text=data['relationship_text'],
            labels=data['labels'],
            rel_freq_year=data['rel_freq_year'],
            rel_type=rel_type,
            heatmap=data['heatmap'],
            heatmap_height=data['heatmap_height'],
            relationship_color=data['relationship_color']
        )

    elif e1_type == "party" and e2_type == "party":
        data = party_vs_party(entity_one, entity_two, rel_type, year_from, year_to)

        if data is None:
            return render_template("no_results.html")

        return render_template(
            "query_party_party.html",
            relationship_text=data['relationship_text'],
            relationship_color=data['relationship_color'],
            relationships=data['relationships_json'],
            party_one=e1_info,
            party_two=e2_info,
            labels=data['labels'],
            rel_freq_year=data['rel_freq_year'])


# render documents from the CHAVE collection
@app.route("/chave")
def chave():
    chave_id = request.args.get("q")
    article = [article for article in chave_publico if article["id"] == chave_id][0]
    article["text"] = article["text"].replace("\n", "<br><br>")
    return render_template("chave_template.html", article=article)


# get all 'other' relationships and shows then in annotation template
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


# other: personalities without image
@app.route("/complete")
def complete():
    result = get_entities_without_image()
    return render_template("incomplete_entities.html", items=result)


# other: personalities only with other rels
@app.route("/only_other")
def only_other():
    results = personalities_only_with_other()
    return render_template("incomplete_entities_no_rels.html", items=results)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
