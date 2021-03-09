from collections import Counter, defaultdict

from politiquices.webapp.webapp.lib.cache import (
    all_entities_info,
    all_parties_info,
    all_parties_members,
    top_co_occurrences,
    wiki_id_info,
)
from politiquices.webapp.webapp.lib.data_models import Person
from politiquices.webapp.webapp.lib.sparql_queries import (
    get_person_relationships_by_year,
    get_wiki_id_affiliated_with_party,
    get_relationship_between_parties,
    get_relationship_between_person_and_party,
    get_relationship_between_party_and_person,
    get_person_info,
    get_relationship_between_two_persons,
    get_all_relationships_between_two_entities,
    get_top_relationships,
    get_person_relationships,
    get_nr_of_persons,
    get_total_nr_of_articles,
    get_nr_articles_per_year,
    get_total_articles_by_year_by_relationship_type,
    get_persons_articles_freq
)

from politiquices.webapp.webapp.lib.utils import (
    determine_heatmap_height,
    fill_zero_values,
    get_chart_labels_min_max,
    get_relationship,
    make_json,
    per_vs_person_linkable, clickable_title, make_https
)


# entity detail
def entity_full_story(wiki_id, annotate):

    # get the person info: name, image, education, office positions, etc.
    person = get_person_info(wiki_id)

    # get all the relationships
    relationships = get_person_relationships(wiki_id)

    # create a clickable title
    opposes = [clickable_title(r, wiki_id) for r in relationships["opposes"]]
    supports = [clickable_title(r, wiki_id) for r in relationships["supports"]]
    opposed_by = [clickable_title(r, wiki_id) for r in relationships["opposed_by"]]
    supported_by = [clickable_title(r, wiki_id) for r in relationships["supported_by"]]

    if annotate:
        other = [clickable_title(r, wiki_id) for r in relationships["other"]]
        other_by = [clickable_title(r, wiki_id) for r in relationships["other_by"]]
        data = {"opposes": opposes,
                "supports": supports,
                "opposed_by": opposed_by,
                "supported_by": supported_by,
                "other": other,
                "other_by": other_by,
                "wiki_id": person.wiki_id,
                "name": person.name,
                "image": make_https(person.image_url),
                "parties": person.parties,
                "positions": person.positions,
                "occupations": person.occupations,
                "education": person.education}
        return data

    # make json objects
    opposed_json = make_json(opposes)
    supported_json = make_json(supports)
    opposed_by_json = make_json(opposed_by)
    supported_by_json = make_json(supported_by)
    all_relationships_json = opposed_json + supported_json + opposed_by_json + supported_by_json

    # get the top-related entities
    top_entities_in_rel_type = get_top_relationships(wiki_id)

    # get the data to create the graph
    chart_js_data = build_relationships_by_year(wiki_id)

    data = {
        # person information
        "wiki_id": person.wiki_id,
        "name": person.name,
        "image": make_https(person.image_url),
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

        # relationships in json for bootstrap-table
        'opposed': opposed_json,
        'supported': supported_json,
        'opposed_by': opposed_by_json,
        'supported_by': supported_by_json,
        'all_relationships': all_relationships_json
    }

    return data


def build_relationships_by_year(wiki_id: str):
    # some personality can support another personality in two different relationship directions
    supported_freq_one = get_person_relationships_by_year(wiki_id, "ent1_supports_ent2", ent="ent1")
    supported_freq_two = get_person_relationships_by_year(wiki_id, "ent2_supports_ent1", ent="ent2")
    supported_freq_sum = Counter(supported_freq_one) + Counter(supported_freq_two)
    supported_freq = {k: supported_freq_sum[k] for k in sorted(supported_freq_sum)}

    # opposes
    opposed_freq_one = get_person_relationships_by_year(wiki_id, "ent1_opposes_ent2", ent="ent1")
    opposed_freq_two = get_person_relationships_by_year(wiki_id, "ent2_opposes_ent1", ent="ent2")
    opposed_freq_sum = Counter(opposed_freq_one) + Counter(opposed_freq_two)
    opposed_freq = {k: opposed_freq_sum[k] for k in sorted(opposed_freq_sum)}

    # supported_by
    supported_by_freq_one = get_person_relationships_by_year(wiki_id, "ent2_supports_ent1", ent="ent1")
    supported_by_freq_two = get_person_relationships_by_year(wiki_id, "ent1_supports_ent2", ent="ent2")
    supported_by_freq_sum = Counter(supported_by_freq_one) + Counter(supported_by_freq_two)
    supported_by_freq = {k: supported_by_freq_sum[k] for k in sorted(supported_by_freq_sum)}

    # opposed_by
    opposed_by_freq_one = get_person_relationships_by_year(wiki_id, "ent2_opposes_ent1", ent="ent1")
    opposed_by_freq_two = get_person_relationships_by_year(wiki_id, "ent1_opposes_ent2", ent="ent2")
    opposed_by_freq_sum = Counter(opposed_by_freq_one) + Counter(opposed_by_freq_two)
    opposed_by_freq = {k: opposed_by_freq_sum[k] for k in sorted(opposed_by_freq_sum)}

    # normalize intervals considering the 4 data points and fill in zero values
    labels = get_chart_labels_min_max()
    opposed_freq = fill_zero_values(labels, opposed_freq)
    supported_freq = fill_zero_values(labels, supported_freq)
    opposed_by_freq = fill_zero_values(labels, opposed_by_freq)
    supported_by_freq = fill_zero_values(labels, supported_by_freq)

    return {
        "labels": labels,
        "opposed_freq": opposed_freq,
        "supported_freq": supported_freq,
        "opposed_by_freq": opposed_by_freq,
        "supported_by_freq": supported_by_freq,
    }


# party members
def get_party_members(wiki_id):
    for x in all_parties_info:
        if x["wiki_id"] == wiki_id:
            party_name = x["party_label"]
            party_logo = x["party_logo"]
            break

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

    return {
        'members': sorted_persons,
        'party_name': party_name,
        'party_logo': party_logo,
        'party_wiki_id': wiki_id
    }


# SPARQL database queries
def party_vs_party(party_a, party_b, rel_text, start_year, end_year):
    """
    Given two parties, looks for relationships between members of both parties, performing
    a kind of cartesian product operation.
    """

    # get the members for each party
    party_a_per = " ".join(["wd:" + x for x in get_wiki_id_affiliated_with_party(party_a)])
    party_b_per = " ".join(["wd:" + x for x in get_wiki_id_affiliated_with_party(party_b)])

    # query the RDF and get the relationships
    _, rel = get_relationship(rel_text)
    results = get_relationship_between_parties(party_a_per, party_b_per, rel, start_year, end_year)

    if len(results) == 0:
        return None

    for r in results:
        per_vs_person_linkable(r)

    relationships_json = make_json([r for r in results if r["rel_type"] == rel])
    rel_freq_year = {year: 0 for year in get_chart_labels_min_max()}

    for r in results:
        rel_freq_year[r["date"][0:4]] += 1

    return {'relationships_json': relationships_json,
            'rel_freq_year': [rel_freq_year[year] for year in rel_freq_year.keys()],
            'labels': get_chart_labels_min_max()}


def person_vs_party(person_wiki_id, party_wiki_id, rel_text, start_year, end_year):
    """
    relationships between an entity and (members of) a party
    """
    gradient, rel = get_relationship(rel_text)
    results = get_relationship_between_person_and_party(
        person_wiki_id, party_wiki_id, rel, start_year, end_year
    )
    if len(results) == 0:
        return None

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

    return {
        'relationships_json': relationships_json,
        'rel_freq_year': [rel_freq_year[year] for year in rel_freq_year.keys()],
        'labels': get_chart_labels_min_max(),
        'heatmap': sorted_heatmap,
        'heatmap_gradient': gradient,
        'heatmap_height': heatmap_height}


def party_vs_person(party_wiki_id, per_wiki_id, rel_text, start_year, end_year):
    """
    relationships between (members of) a party and an entity
    """
    gradient, rel = get_relationship(rel_text)
    results = get_relationship_between_party_and_person(
        party_wiki_id, per_wiki_id, rel, start_year, end_year
    )
    if len(results) == 0:
        return None

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

    return {
        'relationships_json': relationships_json,
        'rel_freq_year': [rel_freq_year[year] for year in rel_freq_year.keys()],
        'labels': get_chart_labels_min_max(),
        'heatmap': sorted_heatmap,
        'heatmap_gradient': gradient,
        'heatmap_height': heatmap_height}


def person_vs_person(per_one, per_two, rel_text, start_year, end_year, annotate):
    _, rel = get_relationship(rel_text)
    results = get_relationship_between_two_persons(per_one, per_two, rel, start_year, end_year)

    if len(results) == 0:
        return None

    for r in results:
        per_vs_person_linkable(r)

    if annotate:
        items = [{"url": r["url"], "date": r["date"], "title": r["title"],
                  "title_clickable": r["title_clickable"], "score": r["score"],
                  "rel_type": r["rel_type"]} for r in results]
        return {'items': items}

    relationships_json = make_json([r for r in results if r["rel_type"] == rel])
    rel_freq_year = {year: 0 for year in get_chart_labels_min_max()}
    for r in results:
        rel_freq_year[r["date"][0:4]] += 1

    data = {
        'relationships': relationships_json,
        'relationship_text': rel_text,
        'labels': get_chart_labels_min_max(),
        'rel_freq_year': [rel_freq_year[year] for year in rel_freq_year.keys()],
        'rel_text': rel_text
    }

    return data


# full-story between 2 entities
def entity_vs_entity(wiki_id_one, wiki_id_two):
    """
    Get all the relationships between two persons, centered in one entity, meaning that
    the relationships are updated to reflect this
    """
    person_one_info = get_person_info(wiki_id_one)
    person_two_info = get_person_info(wiki_id_two)
    results = get_all_relationships_between_two_entities(wiki_id_one, wiki_id_two)
    if len(results) == 0:
        return None

    # ToDo: refactor all this
    def relationships_counter():
        return {
            "ent1_opposes_ent2": 0,
            "ent1_supports_ent2": 0,
            "ent1_opposed_by_ent2": 0,
            "ent1_supported_by_ent2": 0,
        }

    # an entry for each year between the min and max years in the dataset
    rels_freq_by_year = defaultdict(relationships_counter)
    labels = get_chart_labels_min_max()
    for label in labels:
        rels_freq_by_year[label]["ent1_opposes_ent2"] = 0

    for relationship in results:
        ent1_wiki_id = relationship["ent1_wiki"]
        year = relationship["date"][0:4]
        rel_type = relationship["rel_type"]

        if rel_type.startswith("ent1"):
            if ent1_wiki_id != wiki_id_one:
                if "supports" in rel_type:
                    rels_freq_by_year[year]["ent1_supported_by_ent2"] += 1
                    relationship["rel_type_new"] = "ent1_supported_by_ent2"
                if "opposes" in rel_type:
                    rels_freq_by_year[year]["ent1_opposed_by_ent2"] += 1
                    relationship["rel_type_new"] = "ent1_opposed_by_ent2"
            else:
                rels_freq_by_year[year][rel_type] += 1
                relationship["rel_type_new"] = rel_type

        if rel_type.startswith("ent2"):
            if ent1_wiki_id != wiki_id_one:
                if "supports" in rel_type:
                    rels_freq_by_year[year]["ent1_supports_ent2"] += 1
                    relationship["rel_type_new"] = "ent1_supports_ent2"
                if "opposes" in rel_type:
                    rels_freq_by_year[year]["ent1_opposes_ent2"] += 1
                    relationship["rel_type_new"] = "ent1_opposes_ent2"
            else:
                if "supports" in rel_type:
                    rels_freq_by_year[year]["ent1_supported_by_ent2"] += 1
                    relationship["rel_type_new"] = "ent1_supported_by_ent2"
                if "opposes" in rel_type:
                    rels_freq_by_year[year]["ent1_opposed_by_ent2"] += 1
                    relationship["rel_type_new"] = "ent1_opposed_by_ent2"

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

    return {
        # relationships
        'opposed': opposed,
        'supported': supported,
        'opposed_by': opposed_by,
        'supported_by': supported_by,
        'all_relationships': all_json,

        # persons information
        'person_one_info': person_one_info,
        'person_two_info': person_two_info,

        # chart information
        'labels': labels,
        'ent1_opposes_ent2': ent1_opposes_ent2,
        'ent1_supports_ent2': ent1_supports_ent2,
        'ent1_opposed_by_ent2': ent1_opposed_by_ent2,
        'ent1_supported_by_ent2': ent1_supported_by_ent2
    }


# data statistics
def get_stats():
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
    for x in top_co_occurrences:
        co_occurrences_labels.append(x["person_a"]["name"] + " / " + x["person_b"]["name"])
        co_occurrences_values.append(x["nr_occurrences"])

    return {
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
