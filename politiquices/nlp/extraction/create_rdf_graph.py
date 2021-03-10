import argparse
import operator
from enum import Enum
from datetime import datetime
from itertools import groupby
from typing import Set, Optional
from collections import defaultdict
from dataclasses import dataclass

from jsonlines import jsonlines
from rdflib import BNode, Graph, Literal, Namespace, SKOS, URIRef, XSD
from rdflib.namespace import DC, RDFS

from politiquices.nlp.utils.utils import (
    minimize_publico_urls,
    publico_urls,
    read_ground_truth,
    str2bool
)
from politiquices.webapp.webapp.lib.utils import make_https


@dataclass
class Person:
    name: str
    also_known_as: Set[str]
    power_id: Optional[str]
    wikidata_id: str


@dataclass
class Article:
    url: str
    title: str
    source: Optional[str]
    date: Optional[datetime]
    crawled_date: Optional[str]


@dataclass
class RelationshipType(Enum):
    ent1_opposes_ent2 = 1
    ent2_opposes_ent1 = 2
    ent1_supports_ent2 = 3
    ent2_supports_ent1 = 4
    both_agree = 5
    both_disagree = 6
    other = 7


@dataclass
class Relationship:
    url: str
    rel_type: str
    rel_score: float
    ent1: Person
    ent2: Person
    ent1_str: str
    ent2_str: str


def remove_duplicates_with_same_url(f_name):
    """
    discard duplicate URLs
    """
    seen = set()
    unique = []
    duplicate = 0
    for entry in processed_titles(f_name):
        if entry["url"].startswith(publico_urls):
            url = minimize_publico_urls(entry["url"])
        else:
            url = entry["url"]

        if url not in seen:
            unique.append(entry)
            seen.add(url)
        else:
            duplicate += 1

    print(f"Removed {duplicate} URL duplicates")
    return unique


def remove_url_crawled_diff_dates_duplicates(unique_url):
    """
    sort all arquivo.pt articles by original crawled URL and take the oldest version,
    this is to avoid having duplicate titles in politiquices Sparql graph
    """
    articles = []
    for entry in unique_url:
        original_url = "/".join(entry["url"].split("/")[5:])
        articles.append(
            (
                original_url,
                entry["title"],
                entry["date"],
                entry["url"],
                entry["entities"],
                entry["ent_1"],
                entry["ent_2"],
                entry["scores"],
            )
        )

    found_duplicate = 0
    unique = []
    # (original_url, title, tstamp, link, entities, ent_1, ent_2, rel_scores)
    # sort the articles by original url and group by original url, from the group select
    # oldest version
    sorted_articles = sorted(articles, key=operator.itemgetter(0))
    for k, g in groupby(sorted_articles, operator.itemgetter(0)):
        articles = list(g)
        if len(articles) > 1:
            found_duplicate += 1
            earliest = sorted(articles, key=operator.itemgetter(2))[0]
            result = {
                "title": earliest[1],
                "date": earliest[2],
                "url": earliest[3],
                "entities": earliest[4],
                "ent_1": earliest[5],
                "ent_2": earliest[6],
                "scores": earliest[7],
            }
        else:
            article = articles[0]
            result = {
                "title": article[1],
                "date": article[2],
                "url": article[3],
                "entities": article[4],
                "ent_1": article[5],
                "ent_2": article[6],
                "scores": article[7],
            }
        unique.append(result)

    print(f"Removed {found_duplicate} same URL crawled different dates duplicates")

    return unique


def remove_duplicates_same_domain(unique):
    articles = []
    for entry in unique:
        original_url = "/".join(entry["url"].split("/")[5:])
        articles.append(
            (
                original_url,
                entry["title"],
                entry["date"],
                entry["url"],
                entry["entities"],
                entry["ent_1"],
                entry["ent_2"],
                entry["scores"],
            )
        )

    # original_url, title, tstamp, link, entities, ent_1, ent_2, scores
    sorted_articles = sorted(articles, key=operator.itemgetter(1))

    # group by original title, from the group take the oldest one
    articles_unique = []
    for k, g in groupby(sorted_articles, operator.itemgetter(1)):
        arts = list(g)
        earliest = sorted(arts, key=operator.itemgetter(2))[0]
        result = {
            "title": earliest[1],
            "date": earliest[2],
            "url": earliest[3],
            "entities": earliest[4],
            "ent_1": earliest[5],
            "ent_2": earliest[6],
            "scores": earliest[7],
        }
        articles_unique.append(result)

    print(f"{len(articles_unique)} unique articles")

    return articles_unique


def processed_titles(filename):
    with jsonlines.open(filename, mode="r") as reader:
        for line in reader:
            yield line


def extract_date(crawled_date: str, url_type):
    if url_type == "publico":
        try:
            date_obj = datetime.strptime(crawled_date, "%Y-%m-%d %H:%M:%S")
            return datetime.strftime(date_obj, "%Y-%m-%d")
        except ValueError as e:
            raise e

    elif url_type == "chave":
        date_obj = datetime.strptime(crawled_date, "%Y-%m-%d")
        return datetime.strftime(date_obj, "%Y-%m-%d")
        pass

    else:
        year = crawled_date[0:4]
        month = crawled_date[4:6]
        day = crawled_date[6:8]
        hour = crawled_date[8:10]
        minute = crawled_date[10:12]
        second = crawled_date[12:14]
        date_str = f"{year}-{month}-{day}T{hour}:{minute}:{second}"

        # ToDo: remove this check
        if int(year) > 2020:
            raise ValueError(date_str)
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
            return datetime.strftime(date_obj, "%Y-%m-%d")
        except ValueError as e:
            raise e


def build_person(wikidata_id, name, persons):
    """
    Store all the persons to be added to the Graph

    :param wikidata_id:
    :param name:
    :param persons:
    :return:
    """
    if wikidata_id in persons:
        if name != persons[wikidata_id].name:
            persons[wikidata_id].also_known_as.add(name)
    else:
        persons[wikidata_id] = Person(
            name=name, also_known_as=set(), power_id="", wikidata_id=wikidata_id
        )


def process_classified_titles(titles, persons, gold_urls=None):
    relationships = []
    articles = []

    for title in titles:

        # ignore empty URLs or URLs part of the gold-data
        url = title["url"]
        if url == "None" or url == "\\N" or url in gold_urls:
            continue

        # ignore titles where both entities are the same
        e1_wiki = title["ent_1"]["wiki"]
        e2_wiki = title["ent_2"]["wiki"]
        if e1_wiki == e2_wiki:
            continue

        scores = [(k, v) for k, v in title["scores"].items()]
        rel_type = sorted(scores, key=lambda x: x[1], reverse=True)[0]
        person_1 = title["entities"][0]
        person_2 = title["entities"][1]
        news_title = title["title"].strip()

        # detect article origin
        url_type = "arquivo"
        if url.startswith(publico_urls):
            url_type = "publico"
        elif url.startswith("https://www.linguateca.pt/CHAVE?"):
            url_type = "chave"

        # special case to transform publico.pt urls to: https://publico.pt/<news_id>
        url = minimize_publico_urls(url) if url_type == "publico" else url

        try:
            crawled_date = extract_date(title["date"], url_type)
        except ValueError as e:
            # print(url, '\t', e)
            continue

        p1_id = e1_wiki
        p1_name = person_1
        build_person(p1_id, p1_name, persons)

        p2_id = e2_wiki
        p2_name = person_2
        build_person(p2_id, p2_name, persons)

        relationships.append(
            Relationship(
                url=url,
                rel_type=rel_type[0],
                rel_score=rel_type[1],
                ent1=p1_id,
                ent2=p2_id,
                ent1_str=person_1,
                ent2_str=person_2,
            )
        )

        articles.append(
            Article(url=url, title=news_title, source=None, date=None, crawled_date=crawled_date)
        )

    return articles, persons, relationships


def process_gold(titles):
    persons = defaultdict(Person)
    relationships = []
    articles = []

    for entry in titles:
        if entry["ent1_id"] == 'None' or entry["ent2_id"] == 'None':
            continue

        ent1_id = entry["ent1_id"].split("/")[-1]
        ent2_id = entry["ent2_id"].split("/")[-1]
        build_person(ent1_id, entry["ent1"], persons)
        build_person(ent2_id, entry["ent2"], persons)

        relationships.append(
            Relationship(
                url=entry["url"],
                rel_type=entry["label"],
                rel_score=1.0,
                ent1=ent1_id,
                ent2=ent2_id,
                ent1_str=entry["ent1"],
                ent2_str=entry["ent2"],
            )
        )

        articles.append(
            Article(
                url=make_https(entry["url"]),
                title=entry["title"],
                source=None,
                date=None,
                crawled_date=entry["date"],
            )
        )

    return articles, persons, relationships


def populate_graph(articles, persons, relationships):
    g = Graph()

    ns1 = Namespace("http://www.politiquices.pt/")
    g.bind("politiquices", ns1)

    wiki_prop = Namespace("http://www.wikidata.org/prop/direct/")
    wiki_item = Namespace("http://www.wikidata.org/entity/")
    g.bind("wd", wiki_item)
    g.bind("wdt", wiki_prop)
    # see linked-data vocabularies: https://lov.linkeddata.es/dataset/lov/

    print("adding Persons")
    # add Person triples: <wiki_URI, SKOS.prefLabel, name>
    for wikidata_id, person in persons.items():

        # ToDo: make sure pref name is at least two names: first + surname
        g.add(
            (
                URIRef(f"https://www.wikidata.org/entity/{wikidata_id}"),
                SKOS.prefLabel,
                Literal(person.name, lang="pt"),
            )
        )

        # is this needed? probably to match with wikidata graph?
        # http://www.wikidata.org/wiki/Property:P31     # instance of:
        # https://www.wikidata.org/wiki/Q5              # human
        # to filter in the queries to get only persons and not articles or relationships
        g.add(
            (URIRef(f"https://www.wikidata.org/entity/{wikidata_id}"), wiki_prop.P31, wiki_item.Q5)
        )

        g.add(
            (
                URIRef(f"https://www.wikidata.org/entity/{wikidata_id}"),
                RDFS.label,
                Literal(person.name, lang="pt"),
            )
        )

        for alt_name in person.also_known_as:
            g.add(
                (
                    URIRef(f"https://www.wikidata.org/entity/{wikidata_id}"),
                    SKOS.altLabel,
                    Literal(alt_name, lang="pt"),
                )
            )

    print("adding Articles")
    # add triple Article:
    #   <url, DC.title, title>
    #   <url, DC.data, date)
    for article in articles:
        g.add((URIRef(article.url), DC.title, Literal(article.title, lang="pt")))
        g.add((URIRef(article.url), DC.date, Literal(article.crawled_date, datatype=XSD.date)))

    print("adding Relationships")
    # add relationships as Blank Node:
    for rel in relationships:
        _rel = BNode()
        g.add((_rel, ns1.type, Literal(rel.rel_type)))
        g.add((_rel, ns1.score, Literal(rel.rel_score, datatype=XSD.float)))
        g.add((_rel, ns1.url, URIRef(rel.url)))
        g.add((_rel, ns1.ent1, URIRef(f"https://www.wikidata.org/entity/{rel.ent1}")))
        g.add((_rel, ns1.ent2, URIRef(f"https://www.wikidata.org/entity/{rel.ent2}")))
        g.add((_rel, ns1.ent1_str, Literal(rel.ent1_str)))
        g.add((_rel, ns1.ent2_str, Literal(rel.ent2_str)))

    date_time = datetime.now().strftime("%Y-%m-%d_%H%M")
    f_name = f"politiquices_{date_time}.ttl"
    g.serialize(destination=f_name, format="turtle")
    print("graph has {} statements.".format(len(g)))
    print()
    print("persons      : ", len(persons))
    print("articles     : ", len(articles))
    print("relationships: ", len(relationships))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publico", help="input JSONL file with publico.pt results")
    parser.add_argument("--arquivo", help="input JSONL file with arquivo.pt results")
    parser.add_argument("--chave", help="input JSONL file with CHAVE results")
    parser.add_argument(
        "--annotations",
        type=str2bool,
        nargs="?",
        const=True,
        default=False,
        help="loads ground-truth data into the graph",
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    arquivo = []
    publico = []
    chave = []
    articles_gold = []
    rels_gold = []
    gold_urls = None
    gold_persons = None

    if args.annotations:
        training_data = read_ground_truth("../../politiquices_training_data.tsv")
        articles_gold, gold_persons, rels_gold = process_gold(training_data)
        print("ground truth: ", len(articles_gold), end="\n\n")
        gold_urls = [article.url for article in articles_gold]

    if args.arquivo:
        # remove duplicates: keep only unique urls
        arquivo_unique_url = remove_duplicates_with_same_url(args.arquivo)

        # remove duplicates on same crawled url but different crawl date, keep oldest version
        unique = remove_url_crawled_diff_dates_duplicates(arquivo_unique_url)

        # remove duplicates: (i.e., title + crawl date same, one url is sub-domain of other)
        # ToDo: check if this still happens
        arquivo = remove_duplicates_same_domain(unique)
        print("arquivo.pt: ", len(arquivo), end="\n\n")

    if args.publico:
        publico = remove_duplicates_with_same_url(args.publico)
        print("publico.pt: ", len(publico), end="\n\n")

    if args.chave:
        chave = [entry for entry in processed_titles(args.chave)]
        print("CHAVE     : ", len(chave), end="\n\n")

    # pass all articles, persons which can be the already built persons from annotations or empty
    articles, persons, relationships = process_classified_titles(
        arquivo + publico + chave,
        gold_urls=gold_urls,
        persons=gold_persons
    )

    populate_graph(articles + articles_gold, persons, relationships + rels_gold)


if __name__ == "__main__":
    main()
