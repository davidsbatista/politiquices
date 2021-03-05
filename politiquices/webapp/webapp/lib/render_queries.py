from collections import Counter
from functools import lru_cache

from politiquices.webapp.webapp.lib.sparql_queries import (
    get_person_rels_by_year,
    get_wiki_id_affiliated_with_party,
    get_relationship_between_parties
)

from politiquices.webapp.webapp.lib.utils import (
    get_chart_labels_min_max,
    fill_zero_values,
    get_relationship,
    per_vs_person_linkable,
    make_json
)


@lru_cache
def build_relationships_by_year(wiki_id: str):

    # some personality can support another personality in two different relationship directions
    supported_freq_one = get_person_rels_by_year(wiki_id, "ent1_supports_ent2", ent="ent1")
    supported_freq_two = get_person_rels_by_year(wiki_id, "ent2_supports_ent1", ent="ent2")
    supported_freq_sum = Counter(supported_freq_one) + Counter(supported_freq_two)
    supported_freq = {k: supported_freq_sum[k] for k in sorted(supported_freq_sum)}

    # opposes
    opposed_freq_one = get_person_rels_by_year(wiki_id, "ent1_opposes_ent2", ent="ent1")
    opposed_freq_two = get_person_rels_by_year(wiki_id, "ent2_opposes_ent1", ent="ent2")
    opposed_freq_sum = Counter(opposed_freq_one) + Counter(opposed_freq_two)
    opposed_freq = {k: opposed_freq_sum[k] for k in sorted(opposed_freq_sum)}

    # supported_by
    supported_by_freq_one = get_person_rels_by_year(wiki_id, "ent2_supports_ent1", ent="ent1")
    supported_by_freq_two = get_person_rels_by_year(wiki_id, "ent1_supports_ent2", ent="ent2")
    supported_by_freq_sum = Counter(supported_by_freq_one) + Counter(supported_by_freq_two)
    supported_by_freq = {k: supported_by_freq_sum[k] for k in sorted(supported_by_freq_sum)}

    # opposed_by
    opposed_by_freq_one = get_person_rels_by_year(wiki_id, "ent2_opposes_ent1", ent="ent1")
    opposed_by_freq_two = get_person_rels_by_year(wiki_id, "ent1_opposes_ent2", ent="ent2")
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

    data = {'relationships_json': relationships_json,
            'rel_freq_year': [rel_freq_year[year] for year in rel_freq_year.keys()],
            'labels': get_chart_labels_min_max()}

    return data
