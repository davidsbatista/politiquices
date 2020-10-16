import logging
from collections import defaultdict
from datetime import datetime

from flask import request
from flask import render_template
from app import app

from politiquices.webapp.webapp.app.data_models import OfficePosition, PoliticalParty
from politiquices.webapp.webapp.app.sparql_queries import (
    query_sparql,
    counts,
    nr_articles_per_year,
    nr_of_persons,
    total_nr_of_articles,
    get_all_relationships,
    get_all_relationships_by_month_year,
)
from politiquices.webapp.webapp.app.sparql_queries import initalize


def convert_dates(date: str):
    date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime("%Y %b")


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

cached_list_entities = None


@app.route("/")
def status():
    year, nr_articles_year = nr_articles_per_year()
    nr_persons = nr_of_persons()
    nr_articles = total_nr_of_articles()
    items = {
        "nr_persons": nr_persons,
        "nr_articles": nr_articles,
        "year_labels": year,
        "year_articles": nr_articles_year,
    }
    return render_template("index.html", items=items)


@app.route("/entities")
def list_entities():
    global cached_list_entities
    """
    ToDo: run this on the Makefile, just after the server is launched and cache
    """

    if not cached_list_entities:
        print("Getting entities extra info from wikidata.org")
        entities = query_sparql(initalize(), "local")
        persons = set()
        items_as_dict = dict()
        nr_entities = len(entities["results"]["bindings"])

        print(f"{nr_entities} retrieved")

        for e in entities["results"]["bindings"]:

            # this is just avoid duplicate entities, same entity with two labels
            # ToDo: see how to fix this with a SPARQL query
            url = e["item"]["value"]
            if url in persons:
                continue
            persons.add(url)

            name = e["label"]["value"]
            if "image_url" in e:
                image_url = e["image_url"]["value"]
            else:
                image_url = "/static/images/no_picture.jpg"

            wiki_id = url.split("/")[-1]

            items_as_dict[wiki_id] = {
                "wikidata_url": url,
                "wikidata_id": wiki_id,
                "name": name,
                "nr_articles": 0,
                "image_url": image_url,
            }

        article_counts = query_sparql(counts(), "local")
        for e in article_counts["results"]["bindings"]:
            wiki_id = e["person"]["value"].split("/")[-1]
            nr_articles = int(e["count"]["value"])
            items_as_dict[wiki_id]["nr_articles"] = nr_articles

        items = sorted(list(items_as_dict.values()), key=lambda x: x["nr_articles"], reverse=True)
        cached_list_entities = items

    else:
        items = cached_list_entities

    return render_template("all_entities.html", items=items)


def monthlist_fast(start, end):
    # see: https://stackoverflow.com/questions/34898525/generate-list-of-months-between-interval-in-python
    total_months = lambda dt: dt.month + 12 * dt.year
    mlist = []
    for tot_m in range(total_months(start) - 1, total_months(end)):
        y, m = divmod(tot_m, 12)
        mlist.append(datetime(y, m + 1, 1).strftime("%Y-%b"))
    return mlist


def find_maximum_interval(*args):
    """
    Finds a the maximum and minimum date from a several list of (date, freq) pairs

    :param args: a list of pairs of (date, freq)
    :return:
    """
    min_date = min([list(freq.keys())[0] for freq in args if freq])
    max_date = max([list(freq.keys())[-1] for freq in args if freq])
    return min_date, max_date


def get_all_months(few_months_freq, months_lst):
    year_months_values = defaultdict(int)
    for m in months_lst:
        x = datetime.strptime(m, "%Y-%b")
        key = x.strftime("%Y-%m")
        if key in few_months_freq:
            year_months_values[m] = few_months_freq[key]
        else:
            year_months_values[m] = 0

    return year_months_values


@app.route("/entity")
def detail_entity():
    wiki_id = request.args.get("q")

    opposed = get_all_relationships(wiki_id, "ent1_opposes_ent2")
    supported = get_all_relationships(wiki_id, "ent1_supports_ent2")
    opposed_by = get_all_relationships(wiki_id, "ent1_opposes_ent2", reverse=True)
    supported_by = get_all_relationships(wiki_id, "ent1_supports_ent2", reverse=True)

    # ToDo: see https://www.chartjs.org/samples/latest/scales/time/financial.html
    #           https://www.chartjs.org/docs/latest/axes/cartesian/time.html
    opposed_freq = get_all_relationships_by_month_year(wiki_id, "ent1_opposes_ent2")
    supported_freq = get_all_relationships_by_month_year(wiki_id, "ent1_supports_ent2")
    opposed_by_freq = get_all_relationships_by_month_year(wiki_id, "ent1_opposes_ent2", reverse=True)
    supported_by_freq = get_all_relationships_by_month_year(wiki_id, "ent1_supports_ent2", reverse=True)

    min_date, max_date = find_maximum_interval(
        opposed_freq, supported_freq, opposed_by_freq, supported_by_freq
    )

    min_date_obj = datetime.strptime(min_date, "%Y-%m")
    max_date_obj = datetime.strptime(max_date, "%Y-%m")
    months_lst = monthlist_fast(min_date_obj, max_date_obj)

    opposed_freq_month = get_all_months(opposed_freq, months_lst)
    supported_freq_month = get_all_months(supported_freq, months_lst)
    opposed_by_freq_month = get_all_months(opposed_by_freq, months_lst)
    supported_by_freq_month = get_all_months(supported_by_freq, months_lst)

    year_month_labels = list(opposed_by_freq_month.keys())
    opposed_freq = list(opposed_freq_month.values())
    supported_freq = list(supported_freq_month.values())
    opposed_by_freq = list(opposed_by_freq_month.values())
    supported_by_freq = list(supported_by_freq_month.values())

    # entity info
    query = f"""SELECT DISTINCT ?name ?image_url ?political_partyLabel ?political_party_logo 
                                ?officeLabel ?start ?end
                WHERE {{
                    wd:{wiki_id} rdfs:label ?name filter (lang(?name) = "pt").
                    OPTIONAL {{ wd:{wiki_id} wdt:P18 ?image_url. }}
                    OPTIONAL {{ 
                        wd:{wiki_id} p:P102 ?political_partyStmnt. 
                        ?political_partyStmnt ps:P102 ?political_party. 
                        OPTIONAL {{ ?political_party wdt:P154 ?political_party_logo. }}
                    }}
                    OPTIONAL {{
                        wd:{wiki_id} p:P39 ?officeStmnt.
                        ?officeStmnt ps:P39 ?office.
                        OPTIONAL {{ ?officeStmnt pq:P580 ?start. }}
                        OPTIONAL {{ ?officeStmnt pq:P582 ?end. }}
                    }}
                    SERVICE wikibase:label {{
                        bd:serviceParam wikibase:language "pt". 
                    }}
                }}
            """

    results = query_sparql(query, "wiki")
    name = None
    image_url = None
    parties = []
    offices = []

    for e in results["results"]["bindings"]:
        if not name:
            name = e["name"]['value']

        if not image_url:
            if 'image_url' in e:
                image_url = e["image_url"]["value"]

        # political parties
        party = PoliticalParty(
            name=e["political_partyLabel"]['value'] if 'political_partyLabel' in e else None,
            image_url=e["political_party_logo"]['value'] if 'political_party_logo' in e else None
        )
        if party not in parties:
            parties.append(party)

        # office positions
        if 'officeLabel' in e:
            office_position = OfficePosition(
                start=convert_dates(e["start"]["value"]) if 'start' in e else None,
                end=convert_dates(e["end"]["value"]) if 'end' in e else None,
                position=e["officeLabel"]["value"],
            )
            if office_position not in offices:
                offices.append(office_position)

    items = {
        "wiki_id": wiki_id,
        "name": name,
        "image": image_url,
        'parties': parties,
        "offices": offices,
        "opposed": opposed,
        "supported": supported,
        "opposed_by": opposed_by,
        "supported_by": supported_by,
        "year_month_labels": year_month_labels,
        "opposed_freq": opposed_freq,
        "supported_freq": supported_freq,
        "opposed_by_freq": opposed_by_freq,
        "supported_by_freq": supported_by_freq,
    }

    return render_template("entity_detail.html", items=items)
