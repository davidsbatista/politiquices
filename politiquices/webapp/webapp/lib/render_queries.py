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
    get_total_articles_by_year_by_relationship_type,
    get_persons_articles_freq
)

from politiquices.webapp.webapp.lib.utils import (
    clickable_title,
    determine_heatmap_height,
    fill_zero_values,
    get_chart_labels_min_max,
    get_relationship,
    make_https,
    make_json,
    make_single_json,
    per_vs_person_linkable,
)


# entity full story
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
    person_as_subject, person_as_target = get_top_relationships(wiki_id)

    who_person_opposes = [{'wiki_id': k, 'nr_articles': v, 'name': wiki_id_info[k]['name']}
                          for k, v in person_as_subject['who_person_opposes'].items()]

    who_person_supports = [{'wiki_id': k, 'nr_articles': v, 'name': wiki_id_info[k]['name']}
                           for k, v in person_as_subject['who_person_supports'].items()]

    who_opposes_person = [{'wiki_id': k, 'nr_articles': v, 'name': wiki_id_info[k]['name']}
                          for k, v in person_as_target['who_opposes_person'].items()]

    who_supports_person = [{'wiki_id': k, 'nr_articles': v, 'name': wiki_id_info[k]['name']}
                           for k, v in person_as_target['who_supports_person'].items()]

    top_entities_in_rel_type = {
        "who_person_opposes": sorted(who_person_opposes, key=lambda x: x['nr_articles'], reverse=True),
        "who_person_supports": sorted(who_person_supports, key=lambda x: x['nr_articles'], reverse=True),
        "who_opposes_person": sorted(who_opposes_person, key=lambda x: x['nr_articles'], reverse=True),
        "who_supports_person": sorted(who_supports_person, key=lambda x: x['nr_articles'], reverse=True),
    }

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

        # ChartJS: titles/articles frequency by relationships by year
        "year_labels": chart_js_data["labels"],
        "opposed_freq": chart_js_data["opposed_freq"],
        "supported_freq": chart_js_data["supported_freq"],
        "opposed_by_freq": chart_js_data["opposed_by_freq"],
        "supported_by_freq": chart_js_data["supported_by_freq"],

        # top-persons in each relationship
        "top_relations": top_entities_in_rel_type,

        # bootstrap-table: relationships in JSON
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

    relationships_json = make_json([r for r in results])
    rel_freq_year = {year: 0 for year in get_chart_labels_min_max()}

    for r in results:
        rel_freq_year[r["date"][0:4]] += 1

    return {'relationships_json': relationships_json,
            'rel_freq_year': [rel_freq_year[year] for year in rel_freq_year.keys()],
            'labels': get_chart_labels_min_max()}


def person_vs_party(person_wiki_id, party_wiki_id, rel_text, start_year, end_year):
    """
    Relationships between an entity and (members of) a party
    """
    gradient, rel = get_relationship(rel_text)
    results = get_relationship_between_person_and_party(
        person_wiki_id, party_wiki_id, rel, start_year, end_year
    )
    if len(results) == 0:
        return None

    # ToDo: make this in a single loop
    for r in results:
        per_vs_person_linkable(r)
    relationships_json = make_json([r for r in results])

    # barchart: articles/relationships per year
    rel_freq_year = {year: 0 for year in get_chart_labels_min_max()}

    # heatmap: number of relationships with per from a party throughout the years
    entities_freq_year = defaultdict(lambda: {y: 0 for y in get_chart_labels_min_max()})

    for r in results:
        year = r["date"][0:4]
        wiki_id = r["ent2_wiki"] if r['rel_type'].startswith('ent1') else r["ent1_wiki"]
        name = wiki_id_info[wiki_id.split("/")[-1]]['name']
        entities_freq_year[name][year] += 1
        rel_freq_year[year] += 1

    # transform the counts from above into the heatmap structure needed by the JS lib
    heatmap = [{'name': k, 'data': [{'x': year, 'y': freq} for year, freq in v.items()]}
               for k, v in entities_freq_year.items()]
    sorted_heatmap = sorted(heatmap, key=lambda x: x["name"], reverse=True)
    heatmap_height = determine_heatmap_height(len(sorted_heatmap))

    return {
        'relationships_json': relationships_json,
        'rel_freq_year':  [rel_freq_year[year] for year in rel_freq_year.keys()],
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

    # ToDo: make this in a single loop
    for r in results:
        per_vs_person_linkable(r)
    relationships_json = make_json([r for r in results])

    # barchart: articles/relationships per year
    rel_freq_year = {year: 0 for year in get_chart_labels_min_max()}

    # heatmap: number of relationships with per from a party throughout the years
    entities_freq_year = defaultdict(lambda: {y: 0 for y in get_chart_labels_min_max()})

    for r in results:
        year = r["date"][0:4]
        wiki_id = r["ent1_wiki"] if r['rel_type'].startswith('ent1') else r["ent2_wiki"]
        name = wiki_id_info[wiki_id.split("/")[-1]]['name']
        entities_freq_year[name][year] += 1
        rel_freq_year[year] += 1

    # transform the counts from above into the heatmap structure needed by the JS lib
    heatmap = [{'name': k, 'data': [{'x': year, 'y': freq} for year, freq in v.items()]}
               for k, v in entities_freq_year.items()]
    sorted_heatmap = sorted(heatmap, key=lambda x: x["name"], reverse=True)
    heatmap_height = determine_heatmap_height(len(sorted_heatmap))

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

    relationships_json = make_json([r for r in results])
    rel_freq_year = {year: 0 for year in get_chart_labels_min_max()}
    for r in results:
        rel_freq_year[r["date"][0:4]] += 1

    print(len(relationships_json))

    data = {
        'relationships': relationships_json,
        'relationship_text': rel_text,
        'labels': get_chart_labels_min_max(),
        'rel_freq_year': [rel_freq_year[year] for year in rel_freq_year.keys()],
        'rel_text': rel_text
    }

    return data


# Entity_1 versus Entity_2
def entity_vs_entity(wiki_id_one, wiki_id_two):
    """
    Get all the relationships between two persons, centered around entity, i.e.:

    These remain the same:
        - 'ent1_opposes_ent2' remains 'ent1_opposes_ent2'
        - 'ent1_supports_ent2' remains ent1_supports_ent2'

    These are renamed to make 'wiki_id_one' the target of the relationship
        - ent2_opposes_ent1 becomes becomes 'ent1_opposed_by_ent2'
        - ent2_supports_ent1 becomes becomes 'ent1_supported_by_ent2'
    """
    person_one_info = get_person_info(wiki_id_one)
    person_two_info = get_person_info(wiki_id_two)
    results = get_all_relationships_between_two_entities(wiki_id_one, wiki_id_two)
    if len(results) == 0:
        return None

    # represent relationships as if 'ent_1' is the target of the relationships
    opposes = []
    supports = []
    opposed_by = []
    supported_by = []

    # count the number of each rel_type for each year
    opposes_years_counts = {year: 0 for year in get_chart_labels_min_max()}
    supports_years_counts = {year: 0 for year in get_chart_labels_min_max()}
    opposed_by_years_counts = {year: 0 for year in get_chart_labels_min_max()}
    supported_by_years_counts = {year: 0 for year in get_chart_labels_min_max()}

    for x in results:
        per_vs_person_linkable(x)
        year = x['date'][0:4]

        if x['rel_type'] == 'ent1_opposes_ent2':
            if x['ent1_wiki'] == wiki_id_one:
                opposes.append(make_single_json(x))
                opposes_years_counts[year] += 1
            if x['ent1_wiki'] == wiki_id_two:
                opposed_by.append(make_single_json(x))
                opposed_by_years_counts[year] += 1

        if x['rel_type'] == 'ent2_opposes_ent1':
            if x['ent1_wiki'] == wiki_id_one:
                opposed_by.append(make_single_json(x))
                opposed_by_years_counts[year] += 1
            if x['ent1_wiki'] == wiki_id_two:
                opposes.append(make_single_json(x))
                opposes_years_counts[year] += 1

        if x['rel_type'] == 'ent1_supports_ent2':
            if x['ent1_wiki'] == wiki_id_one:
                supports.append(make_single_json(x))
                supports_years_counts[year] += 1
            if x['ent1_wiki'] == wiki_id_two:
                supported_by.append(make_single_json(x))
                supported_by_years_counts[year] += 1

        if x['rel_type'] == 'ent2_supports_ent1':
            if x['ent1_wiki'] == wiki_id_one:
                supported_by.append(make_single_json(x))
                supported_by_years_counts[year] += 1
            if x['ent1_wiki'] == wiki_id_two:
                supports.append(make_single_json(x))
                supports_years_counts[year] += 1

    all_json = opposes + supports + opposed_by + supported_by

    return {
        # persons information
        'person_one_info': person_one_info,
        'person_two_info': person_two_info,

        # relationships
        'opposed': opposes,
        'supported': supports,
        'opposed_by': opposed_by,
        'supported_by': supported_by,
        'all_relationships': all_json,

        # chart information: note: ChartJS expects a list of values for the 'y' axis
        'labels': get_chart_labels_min_max(),
        'ent1_opposes_ent2': list(opposes_years_counts.values()),
        'ent1_supports_ent2': list(supports_years_counts.values()),
        'ent1_opposed_by_ent2': list(opposed_by_years_counts.values()),
        'ent1_supported_by_ent2': list(supported_by_years_counts.values())
    }


# data statistics
def get_stats():

    # number of persons, parties, articles
    nr_persons = get_nr_of_persons()
    nr_parties = len(all_parties_info)

    # total nr of article with and without 'other' relationships
    nr_all_articles, nr_all_no_other_articles = get_total_nr_of_articles()

    # articles per relationship type per year; the sparql query returns results for each rel_type
    # but we aggregate relationships: 'opposes', 'supports, i.e., discard direction and 'other'
    all_years = get_chart_labels_min_max()
    values = get_total_articles_by_year_by_relationship_type()
    aggregated_values = defaultdict(lambda: {'opposes': 0, 'supports': 0})
    for year in all_years:
        if year in values.keys():
            for rel, freq in values[year].items():
                if 'opposes' in rel:
                    aggregated_values[year]['opposes'] += int(freq)
                if 'supports' in rel:
                    aggregated_values[year]['supports'] += int(freq)
        else:
            aggregated_values[year]['opposes'] = 0
            aggregated_values[year]['supports'] = 0

    # personalities frequency chart
    per_freq_labels = []
    per_freq_values = []
    per_freq = get_persons_articles_freq()
    for x in per_freq:
        per_freq_labels.append(wiki_id_info[x["person"].split("/")[-1]]["name"])
        per_freq_values.append(x["freq"])

    # personalities co-occurrence chart
    co_occurrences_labels = []
    co_occurrences_values = []
    for x in top_co_occurrences:
        co_occurrences_labels.append(x["person_a"]["name"] + " / " + x["person_b"]["name"])
        co_occurrences_values.append(x["nr_occurrences"])

    return {
        "nr_parties": nr_parties,
        "nr_persons": nr_persons,
        "nr_all_no_other_articles": nr_all_no_other_articles,

        "nr_articles_year_labels": all_years,
        "supports": [aggregated_values[year]['supports'] for year in aggregated_values],
        "opposes": [aggregated_values[year]['opposes'] for year in aggregated_values],

        "per_freq_labels": per_freq_labels[0:500],
        "per_freq_values": per_freq_values[0:500],
        "per_co_occurrence_labels": co_occurrences_labels[0:500],
        "per_co_occurrence_values": co_occurrences_values[0:500],
    }
