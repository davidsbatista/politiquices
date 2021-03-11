import json
from collections import defaultdict

from politiquices.webapp.webapp.config import static_data
from politiquices.webapp.webapp.lib.sparql_queries import (
    get_all_parties_with_members_count,
    get_nr_relationships_as_subject,
    get_nr_relationships_as_target,
    get_persons_co_occurrences_counts,
    get_persons_wiki_id_name_image_url,
    get_total_nr_articles_for_each_person,
    get_wiki_id_affiliated_with_party
)


def get_entities():
    """
    Get for each personality:
    - name
    - image url
    - wikidata url
    - wikidata id
    - nr articles (not counting other)
    """
    personalities = get_persons_wiki_id_name_image_url()
    wiki_id_nr_articles = get_total_nr_articles_for_each_person()
    for wiki_id, nr_articles in wiki_id_nr_articles.items():
        if wiki_id in personalities:
            personalities[wiki_id]["nr_articles"] = nr_articles
    return sorted(list(personalities.values()), key=lambda x: x["nr_articles"], reverse=True)


def personalities_json_cache():
    """
    Generates JSONs from SPARQL queries:
        - 'all_entities_info.json': a list of of dicts: name, image_url, nr_articles
        - 'wiki_id_info.json': a mapping from wiki_id -> person_info
        - 'persons.json': a sorted list by name of tuples (person_name, wiki_id)
    """

    # persons cache
    per_data = get_entities()
    print(f"{len(per_data)} entities card info (positions + wikidata_link + image + nr articles)")

    with open(static_data + "all_entities_info.json", "w") as f_out:
        json.dump(per_data, f_out, indent=4)

    wiki_id = {
        x["wiki_id"]: {
            "name": x["name"],
            "image_url": x["image_url"],
            "nr_articles": x['nr_articles']}
        for x in per_data
    }
    with open(static_data + "wiki_id_info.json", "w") as f_out:
        json.dump(wiki_id, f_out, indent=4)

    # persons cache for search box
    persons = [{"name": x["name"], "wiki_id": x["wiki_id"]}
               for x in sorted(per_data, key=lambda x: x["name"])]
    all_politiquices_persons = set([x["wiki_id"] for x in persons])
    with open(static_data + "persons.json", "wt") as f_out:
        json.dump(persons, f_out, indent=True)

    return all_politiquices_persons, wiki_id


def parties_json_cache(all_politiquices_persons):

    # rename parties names to include short-forms
    parties_mapping = {
        "Bloco de Esquerda": "BE - Bloco de Esquerda",
        "Coliga\u00e7\u00e3o Democr\u00e1tica Unit\u00e1ria":
            "CDU - Coliga\u00e7\u00e3o Democr\u00e1tica Unit\u00e1ria (PCP-PEV)",
        "Juntos pelo Povo": "JPP - Juntos pelo Povo",
        "Partido Comunista Portugu\u00eas": "PCP - Partido Comunista Portugu\u00eas",
        "Partido Social Democrata": "PSD - Partido Social Democrata",
        "Partido Socialista": "PS - Partido Socialista",
        "Partido Socialista Revolucion\u00e1rio": "PSR - Partido Socialista Revolucion\u00e1rio",
        "Partido Democr\u00e1tico Republicano": "PDR - Partido Democr\u00e1tico Republicano",
        "Pessoas\u2013Animais\u2013Natureza": "PAN - Pessoas\u2013Animais\u2013Natureza",
        "Partido Comunista dos Trabalhadores Portugueses":
            "PCTP/MRPP - Partido Comunista dos Trabalhadores Portugueses",
        "RIR": "RIR - Reagir Incluir Reciclar",
        "Partido da Terra": "MPT - Partido da Terra",
    }

    # parties cache
    parties_data = get_all_parties_with_members_count()
    print(f"{len(parties_data)} parties info (image + nr affiliated personalities)")
    with open(static_data + "all_parties_info.json", "w") as f_out:
        json.dump(parties_data, f_out, indent=4)

    # parties cache for search box, filtering only portuguese political parties
    parties = [
        {
            "name": parties_mapping.get(x["party_label"], x["party_label"]),
            "wiki_id": x["wiki_id"],
        }
        for x in sorted(parties_data, key=lambda x: x["party_label"])
        if x["party_country"] == "Portugal"
    ]
    with open(static_data + "parties.json", "w") as f_out:
        json.dump(parties, f_out, indent=4)

    # members of each party
    party_members = defaultdict(list)
    for party in parties_data:

        # get all wiki_id associated with a party
        wiki_ids = get_wiki_id_affiliated_with_party(party["wiki_id"])

        # then filter only those with mention in new articles
        wiki_ids_in_politiquices = list(set(wiki_ids).intersection(all_politiquices_persons))
        party_members[party["wiki_id"]] = wiki_ids_in_politiquices

    with open(static_data + "party_members.json", "w") as f_out:
        json.dump(party_members, f_out, indent=4)


def entities_top_co_occurrences(wiki_id):
    raw_counts = get_persons_co_occurrences_counts()
    co_occurrences = []
    for x in raw_counts:
        co_occurrences.append(
            {
                "person_a": wiki_id[x["person_a"].split("/")[-1]],
                "person_b": wiki_id[x["person_b"].split("/")[-1]],
                "nr_occurrences": x["n_artigos"],
            }
        )
    with open(static_data + "top_co_occurrences.json", "w") as f_out:
        json.dump(co_occurrences, f_out, indent=4)
    print(f"{len(co_occurrences)} entity co-occurrences")


def persons_relationships_counts_by_type():
    opposes_subj = get_nr_relationships_as_subject("opposes")
    supports_subj = get_nr_relationships_as_subject("supports")
    opposes_target = get_nr_relationships_as_target("opposes")
    supports_target = get_nr_relationships_as_target("supports")

    def relationships_types():
        return {
            "opposes": 0,
            "supports": 0,
            "is_opposed": 0,
            "is_supported": 0,
        }

    relationships = defaultdict(lambda: relationships_types())

    for entry in opposes_subj:
        relationships[entry[0]]["opposes"] += entry[1]

    for entry in supports_subj:
        relationships[entry[0]]["supports"] += entry[1]

    for entry in opposes_target:
        relationships[entry[0]]["is_opposed"] += entry[1]

    for entry in supports_target:
        relationships[entry[0]]["is_supported"] += entry[1]

    with open(static_data + "person_relationships_counts.json", "wt") as f_out:
        json.dump(relationships, f_out, indent=True)


def main():

    print("\nCaching and pre-computing static stuff from SPARQL engine :-)")

    # get all personalities cache
    all_politiquices_persons, wiki_id = personalities_json_cache()

    # parties cache
    parties_json_cache(all_politiquices_persons)

    # entities co-occurrences cache
    entities_top_co_occurrences(wiki_id)

    # unique number of relationships for each person
    persons_relationships_counts_by_type()


if __name__ == "__main__":
    main()
