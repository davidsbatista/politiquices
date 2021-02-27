import json
import logging
from collections import defaultdict

import networkx as nx
from app import app
from flask import request, jsonify
from flask import render_template
from networkx.algorithms.community import k_clique_communities

from politiquices.webapp.webapp.utils.data_models import Person
from politiquices.webapp.webapp.app.neo4j import Neo4jConnection
from politiquices.webapp.webapp.utils.sparql_queries import (
    build_relationships_by_year,
    get_entities_without_image,
    get_nr_articles_per_year,
    get_nr_of_persons,
    get_person_info,
    get_person_relationships,
    get_relationships_between_two_entities,
    get_top_relationships,
    get_total_nr_of_articles,
    get_wiki_id_affiliated_with_party,
    list_of_spec_relations_between_two_persons,
    list_of_spec_relations_between_a_person_and_members_of_a_party,
    list_of_spec_relations_between_members_of_a_party_with_someone,
    list_of_spec_relations_between_two_parties,
    all_persons_freq,
    get_total_articles_by_year_by_relationship_type,
    get_all_other_to_annotate,
)
from politiquices.webapp.webapp.utils.utils import (
    clickable_title,
    make_json,
    get_relationship,
    per_vs_person_linkable,
    get_chart_labels_min_max,
    determine_heatmap_height,
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

with open("webapp/app/static/json/CHAVE-Publico_94_95.jsonl") as f_in:
    chave_publico = [json.loads(line) for line in f_in]

# number of entity cards to read when scrolling down
entities_batch_size = 16


# Entry Page
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


# Estatísticas
@app.route("/stats")
def status():
    # single values
    nr_persons = get_nr_of_persons()
    nr_parties = len(all_parties_info)

    # articles per year chart
    nr_articles_year_labels, nr_articles_year_values = get_nr_articles_per_year()
    nr_articles = get_total_nr_of_articles()

    # articles per relationship type per year chart
    values = get_total_articles_by_year_by_relationship_type()

    """
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
    """

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

        "per_freq_labels": None,  # per_freq_labels,
        "per_freq_values": None,  # per_freq_values,
        "per_co_occurrence_labels": None,  # co_occurrences_labels,
        "per_co_occurrence_values": None,  # co_occurrences_values,
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


# to render documents from the CHAVE collection
@app.route("/chave")
def chave():
    chave_id = request.args.get("q")
    article = [article for article in chave_publico if article["id"] == chave_id][0]
    article["text"] = article["text"].replace("\n", "<br><br>")
    return render_template("chave_template.html", article=article)


@app.route("/annotate")
def annotate():
    to_annotate = get_all_other_to_annotate()

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
    if len(results) == 0:
        return render_template("no_results.html")

    for r in results:
        per_vs_person_linkable(r)

    opposed = make_json([r for r in results if r["rel_type_new"] == "ent1_opposes_ent2"])
    supported = make_json([r for r in results if r["rel_type_new"] == "ent1_supports_ent2"])
    opposed_by = make_json([r for r in results if r["rel_type_new"] == "ent1_opposed_by_ent2"])
    supported_by = make_json([r for r in results if r["rel_type_new"] == "ent1_supported_by_ent2"])
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


def person_vs_person(
        person_one,
        person_two,
        rel_text,
        person_one_info,
        person_two_info,
        start_year=None,
        end_year=None,
        html=False,
):
    gradient, rel = get_relationship(rel_text)
    results = list_of_spec_relations_between_two_persons(
        person_one, person_two, rel, start_year, end_year
    )

    if len(results) == 0:
        return render_template("no_results.html")

    for r in results:
        per_vs_person_linkable(r)

    if "annotate" in request.args:
        items = []
        for r in results:
            items.append(
                {
                    "url": r["url"],
                    "date": r["date"],
                    "title": r["title"],
                    "title_clickable": r["title_clickable"],
                    "score": r["score"],
                    "rel_type": r["rel_type"],
                }
            )

        return render_template(
            "query_person_person_annotate.html",
            entity_one=person_one_info,
            entity_two=person_two_info,
            items=items,
        )

    relationships_json = make_json([r for r in results if r["rel_type"] == rel])
    rel_freq_year = {year: 0 for year in get_chart_labels_min_max()}
    for r in results:
        rel_freq_year[r["date"][0:4]] += 1

    if html:
        return render_template(
            "query_person_person_full.html",
            relationship_text=rel_text,
            relationships=relationships_json,
            person_one=person_one_info,
            person_two=person_two_info,
            labels=get_chart_labels_min_max(),
            rel_freq_year=[rel_freq_year[year] for year in rel_freq_year.keys()],
            rel_text=rel_text,
        )

    return render_template(
        "query_person_person.html",
        relationship_text=rel_text,
        relationships=relationships_json,
        person_one=person_one_info,
        person_two=person_two_info,
        labels=get_chart_labels_min_max(),
        rel_freq_year=[rel_freq_year[year] for year in rel_freq_year.keys()],
        rel_text=rel_text,
    )


def party_vs_person(
        party_wiki_id, person_wiki_id, rel_text, party_info, person_info, start_year, end_year
):
    """
    relationships between (members of) a party and an entity
    """
    gradient, rel = get_relationship(rel_text)
    results = list_of_spec_relations_between_members_of_a_party_with_someone(
        party_wiki_id, person_wiki_id, rel, start_year, end_year
    )
    if len(results) == 0:
        return render_template("no_results.html")

    for r in results:
        per_vs_person_linkable(r)
    relationships_json = make_json([r for r in results if r["rel_type"] == rel])

    # heatmap # ToDo: make this in a single loop
    heatmap = []
    entities_freq_year = defaultdict(lambda: defaultdict(int))
    labels = get_chart_labels_min_max()
    for r in results:
        # ToDo: make map of the cache to avoid this linear search
        wiki_id = r["ent1_wiki"].split("/")[-1]
        name = [p["name"] for p in all_entities_info if p["wiki_id"] == wiki_id][0]
        year = r["date"][0:4]
        entities_freq_year[name][year] += 1

    for name in entities_freq_year.keys():
        per_freq_year = []
        for year in labels:
            if year in entities_freq_year[name]:
                per_freq_year.append({"x": year, "y": entities_freq_year[name][year]})
            else:
                per_freq_year.append({"x": year, "y": 0})
        heatmap.append({"name": name, "data": per_freq_year})
    sorted_heatmap = sorted(heatmap, key=lambda x: x["name"], reverse=True)
    heatmap_height = determine_heatmap_height(len(sorted_heatmap))

    # chart: news articles/relationships per year
    rel_freq_year = {year: 0 for year in get_chart_labels_min_max()}
    for r in results:
        rel_freq_year[r["date"][0:4]] += 1

    return render_template(
        "query_party_person.html",
        relationship_text=rel_text,
        relationships=relationships_json,
        party=party_info,
        person=person_info,
        labels=get_chart_labels_min_max(),
        rel_freq_year=[rel_freq_year[year] for year in rel_freq_year.keys()],
        rel_text=rel_text,
        heatmap=sorted_heatmap,
        heatmap_gradient=gradient,
        heatmap_height=heatmap_height,
    )


def person_vs_party(
        person_wiki_id, party_wiki_id, rel_text, person_info, party_info, start_year, end_year
):
    """
    relationships between an entity and (members of) a party
    """
    gradient, rel = get_relationship(rel_text)
    results = list_of_spec_relations_between_a_person_and_members_of_a_party(
        person_wiki_id, party_wiki_id, rel, start_year, end_year
    )
    if len(results) == 0:
        return render_template("no_results.html")

    for r in results:
        per_vs_person_linkable(r)

    relationships_json = make_json([r for r in results if r["rel_type"] == rel])

    # heatmap # ToDo: make this in a single loop
    heatmap = []
    entities_freq_year = defaultdict(lambda: defaultdict(int))
    labels = get_chart_labels_min_max()
    for r in results:
        # ToDo: make map of the cache to avoid this linear search
        wiki_id = r["ent2_wiki"].split("/")[-1]
        name = [p["name"] for p in all_entities_info if p["wiki_id"] == wiki_id][0]
        year = r["date"][0:4]
        entities_freq_year[name][year] += 1

    for name in entities_freq_year.keys():
        per_freq_year = []
        for year in labels:
            if year in entities_freq_year[name]:
                per_freq_year.append({"x": year, "y": entities_freq_year[name][year]})
            else:
                per_freq_year.append({"x": year, "y": 0})
        heatmap.append({"name": name, "data": per_freq_year})
    sorted_heatmap = sorted(heatmap, key=lambda x: x["name"], reverse=True)
    heatmap_height = determine_heatmap_height(len(sorted_heatmap))

    # chart: news articles/relationships per year
    rel_freq_year = {year: 0 for year in get_chart_labels_min_max()}
    for r in results:
        rel_freq_year[r["date"][0:4]] += 1

    return render_template(
        "query_person_party.html",
        relationship_text=rel_text,
        relationships=relationships_json,
        person=person_info,
        party=party_info,
        labels=get_chart_labels_min_max(),
        rel_freq_year=[rel_freq_year[year] for year in rel_freq_year.keys()],
        rel_text=rel_text,
        heatmap=sorted_heatmap,
        heatmap_gradient=gradient,
        heatmap_height=heatmap_height,
    )


def party_vs_party(party_a, party_b, rel_text, party_a_info, party_b_info, start_year, end_year):
    """
    relationships between (members of) a party and (members of) another party
    """
    party_a_members = " ".join(["wd:" + x for x in get_wiki_id_affiliated_with_party(party_a)])
    party_b_members = " ".join(["wd:" + x for x in get_wiki_id_affiliated_with_party(party_b)])

    _, rel = get_relationship(rel_text)

    results = list_of_spec_relations_between_two_parties(
        party_a_members, party_b_members, rel, start_year, end_year
    )
    if len(results) == 0:
        return render_template("no_results.html")

    for r in results:
        per_vs_person_linkable(r)

    relationships_json = make_json([r for r in results if r["rel_type"] == rel])

    rel_freq_year = {year: 0 for year in get_chart_labels_min_max()}
    for r in results:
        rel_freq_year[r["date"][0:4]] += 1

    return render_template(
        "query_party_party.html",
        relationship_text=rel_text,
        relationships=relationships_json,
        party_one=party_a_info,
        party_two=party_b_info,
        labels=get_chart_labels_min_max(),
        rel_freq_year=[rel_freq_year[year] for year in rel_freq_year.keys()],
        rel_text=rel_text,
    )


@app.route("/graph")
def graph():
    relation = "ACUSA|APOIA"
    year_from = "2000"
    year_to = "2019"
    freq_min = 10
    freq_max = 30
    k_clique = 3

    print(request.args)

    if "freq_min" in request.args:
        freq_min = int(request.args.get("freq_min"))

    if "freq_max" in request.args:
        freq_max = int(request.args.get("freq_max"))

    if "rel_type" in request.args:
        rel_type = request.args.get("rel_type")
        if rel_type == "supports":
            relation = "APOIA"
        elif rel_type == "opposes":
            relation = "ACUSA"
        else:
            relation = "ACUSA|APOIA"

    if "k_clique" in request.args:
        k_clique = int(request.args.get("k_clique"))

    if "year_from" in request.args and "year_to" in request.args:
        year_from = request.args.get("year_from")
        year_to = request.args.get("year_to")

    query = (
        f"MATCH (s)-[r:{relation}]->(t) "
        f"WHERE r.data >= date('{year_from}-01-01') AND r.data <= date('{year_to}-12-31') "
        "RETURN s, t, r"
    )

    conn = Neo4jConnection(uri="bolt://localhost:7687", user="neo4j", pwd="s3cr3t")
    results = conn.query(query)
    conn.close()

    # build the nodes structure to pass to vis js network and counts edges with counts
    nodes_info = {}
    edges_agg = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for x in results:
        if x["s"].id not in nodes_info:
            nodes_info[x["s"]["id"]] = {
                "id": x["s"]["id"],
                "label": x["s"]["name"],
                "color": {
                    "border": "#2B7CE9",
                    "background": "#97C2FC",
                    "highlight": {"border": "#2B7CE9", "background": "#D2E5FF"},
                },
            }
        if x["t"].id not in nodes_info:
            nodes_info[x["t"]["id"]] = {
                "id": x["t"]["id"],
                "label": x["t"]["name"],
                "color": {
                    "border": "#2B7CE9",
                    "background": "#97C2FC",
                    "highlight": {"border": "#2B7CE9", "background": "#D2E5FF"},
                },
            }
        edges_agg[x["r"].type][x["r"].start_node["id"]][x["r"].end_node["id"]] += 1

    # filter to show only edges within: freq_min <= freq <= freq_max
    # and nodes connected to these edges
    edges = []
    nodes_in_graph = []

    tmp_edges = defaultdict(list)
    bidirectional_edges = defaultdict(list)

    for rel_type, rels in edges_agg.items():
        for s, targets in rels.items():
            for t, freq in targets.items():
                if freq_min <= freq <= freq_max:

                    if rel_type == "ACUSA":
                        rel_text = "opõe-se"
                        color = "#FF0000"
                        highlight = "#780000"
                    else:
                        rel_text = "apoia"
                        color = "#44861E"
                        highlight = "#1d4a03"

                    edges.append(
                        {
                            "from": s,
                            "to": t,
                            "id": len(edges) + 1,
                            "color": {
                                "color": color,
                                "highlight": highlight,
                            },
                            "scaling": {"max": 7},
                            "label": rel_text,
                            "value": freq,
                        }
                    )
                    nodes_in_graph.append(s)
                    nodes_in_graph.append(t)

                    # extract bi-directional relationship
                    tmp_edges[s].append(t)
                    if s in tmp_edges[t]:
                        bidirectional_edges[s].append(t)

    nodes = [node_info for node_id, node_info in nodes_info.items() if node_id in nodes_in_graph]

    # build a networkx structure, compute communities
    networkx_nodes = []
    networkx_edges = []
    for node, other in bidirectional_edges.items():
        for n in other:
            networkx_edges.append((node, n))

    for edge in networkx_edges:
        networkx_nodes.append(edge[0])
        networkx_nodes.append(edge[1])

    g = nx.Graph()
    g.add_nodes_from(networkx_nodes)
    g.add_edges_from(networkx_edges)
    communities_colors = {
        0: "#33ff49",
        1: "#4363d84",
        2: "#f582315",
        3: "#911eb46",
        4: "#42d4f47",
        5: "#f032e68",
        6: "#bfef459",
        7: "#fabed410",
        8: "#46999011",
        9: "#dcbeff12",
        10: "#9A632413",
        11: "#fffac814",
        12: "#80000015",
        13: "#aaffc316",
        14: "#80800017",
        15: "#ffd8b118",
        16: "#00007519",
        17: "#a9a9a",
    }

    # set node size as the value of the pagerank
    page_rank_values = nx.pagerank(g)
    for k, v in page_rank_values.items():
        for node in nodes:
            if node["id"] == k:
                node["value"] = v

    if k_clique > 1:
        # add communities color to nodes_info
        communities = list(k_clique_communities(g, k_clique))
        for idx, c in enumerate(communities):
            for n in c:
                for node in nodes:
                    if node["id"] == n:
                        node["color"] = {
                            "border": "#222222",
                            "background": communities_colors[idx],
                            "highlight": {"border": "#2B7CE9", "background": "#D2E5FF"},
                        }

    # return and render the results
    if "rel_type" in request.args:
        return jsonify({"nodes": nodes, "edges": edges})

    return render_template("graph.html", nodes=nodes, edges=edges)


@app.route("/queries")
def queries():
    print(request.args)
    query_nr = request.args.get("query_nr")

    if query_nr == "two":
        entity_one = request.args.get("e1")
        entity_two = request.args.get("e2")
        return entity_vs_entity(entity_one, entity_two)

    if query_nr == "one":

        html = False

        # NOTE: this is all very very hacky...scary!
        year_from = request.args.get("year_from")
        year_to = request.args.get("year_to")
        year = request.args.get("year")
        if year and (not year_from and not year_to):
            year_from = year
            year_to = year

        if "html" in request.args:
            html = True

        entity_one = request.args.get("e1")
        entity_two = request.args.get("e2")
        rel_text = request.args.get("relationship")
        e1_info, e1_type = get_info(entity_one)
        e2_info, e2_type = get_info(entity_two)

        if e1_type == "person" and e2_type == "person":
            return person_vs_person(
                entity_one,
                entity_two,
                rel_text,
                e1_info,
                e2_info,
                start_year=year_from,
                end_year=year_to,
                html=html,
            )

        elif e1_type == "party" and e2_type == "person":
            return party_vs_person(
                entity_one,
                entity_two,
                rel_text,
                e1_info,
                e2_info,
                start_year=year_from,
                end_year=year_to,
            )

        elif e1_type == "person" and e2_type == "party":
            return person_vs_party(
                entity_one,
                entity_two,
                rel_text,
                e1_info,
                e2_info,
                start_year=year_from,
                end_year=year_to,
            )

        elif e1_type == "party" and e2_type == "party":
            return party_vs_party(
                entity_one,
                entity_two,
                rel_text,
                e1_info,
                e2_info,
                start_year=year_from,
                end_year=year_to,
            )
