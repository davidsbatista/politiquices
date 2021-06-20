import re
import argparse
import operator
from enum import Enum
from datetime import datetime
from itertools import groupby
from typing import Set, Optional
from collections import defaultdict
from dataclasses import dataclass

from jsonlines import jsonlines
from rdflib.namespace import DC
from rdflib import BNode, Graph, Literal, Namespace, SKOS, URIRef, XSD

from politiquices.nlp.utils.utils import (
    minimize_publico_urls,
    publico_urls,
    read_ground_truth,
    str2bool,
)
from politiquices.webapp.webapp.lib.utils import make_https


@dataclass
class Person:
    known_as: Set[str]
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
    - Minimizes all publico.pt urls to https://publico.pt/<id>
    - Discard duplicate URLs
    - Returns unique publico articles/titles with minimized URLs
    """
    seen = set()
    unique = []
    duplicate = 0

    for entry in processed_titles(f_name):

        minimized_url = entry["url"]

        if entry["url"].startswith(publico_urls):
            minimized_url = minimize_publico_urls(entry["url"])

        if minimized_url not in seen:
            entry['url'] = minimized_url
            unique.append(entry)
            seen.add(minimized_url)
        else:
            duplicate += 1

    # print(f"Removed {duplicate} URL duplicates")
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

    # print(f"Removed {found_duplicate} same URL crawled different dates duplicates")

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

    # print(f"{len(articles_unique)} unique articles")

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

    else:
        year = crawled_date[0:4]
        month = crawled_date[4:6]
        day = crawled_date[6:8]
        hour = crawled_date[8:10]
        minute = crawled_date[10:12]
        second = crawled_date[12:14]
        date_str = f"{year}-{month}-{day}T{hour}:{minute}:{second}"
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
        persons[wikidata_id].known_as.add(name)
    else:
        persons[wikidata_id] = Person(known_as={name}, power_id="", wikidata_id=wikidata_id)


def is_discardable(title):
    """
    Ignore articles:
    - 1. which have empty URLs, since we cannot reach the whole news article
    - 2. ent1 and ent2 are the same

    """

    # ignore empty URLs
    url = title["url"]
    if url == "None" or url == "\\N":
        return True

    # ignore titles where both entities are the same
    if title["ent_1"]["wiki_id"] == title["ent_2"]["wiki_id"]:
        return True


def is_in_gold_data(title, url_type, gold_urls):
    """
    Check if an URL is part of the golden data which is already processed

    NOTE:
        arquivo.pt urls can contain crawled publico.pt urls that are also in the golden
        data but as publico.pt urls;  those need to be converted from long arquivo.pt url to
        publico short url, so that duplicates with golden-data can be detected;

        The URLs in 'exceptions' are publico.pt URLs which can be part of arquivo.pt but are ignored
    """

    exceptions = ["http://www.publico.pt/ar95/noticias/", "http://www.publico.pt/publico/1999/"]

    url = title["url"]
    if url in gold_urls:
        return True

    # try to see if contains a publico.pt URL
    if url_type == "arquivo" and not any(x in url for x in exceptions):
        match = re.match(r"https://arquivo.*(https?:\/\/w?w?w?\.?publico\.pt[^?]+)", url)
        url = minimize_publico_urls(match.group(1)) if match else url
        if url in gold_urls:
            return True

    return False


def detect_source_from_url(title):
    """
    Detects the origin of an article:
        - CHAVE
        - publico.pt
        - arquivo.pt
    """
    if title["url"].startswith("https://www.linguateca.pt/CHAVE?"):
        return "chave"
    elif title["url"].startswith('https://publico.pt'):
        return "publico"
    return "arquivo"


def get_publico_urls_in_arquivo(articles):
    arquivo_publico_urls = []
    for article in articles:
        for url in re.finditer(r"https?:\/\/w?w?w?\.?publico\.pt[^?]+", article["url"]):
            publico_url = url.group()
            try:
                publico_id = int(publico_url.split("-")[-1])
                arquivo_publico_urls.append(f"https://publico.pt/{publico_id}")
            except ValueError as e:
                try:
                    publico_id = int(publico_url.split("_")[-1])
                    arquivo_publico_urls.append(f"https://publico.pt/{publico_id}")
                except ValueError as e:
                    try:
                        publico_id = int(publico_url.split("/amp")[0].split("-1")[-1])
                        arquivo_publico_urls.append(f"https://publico.pt/{publico_id}")
                    except ValueError as e:
                        # print("could net get id for ", publico_url)
                        continue
    return arquivo_publico_urls


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


def process_data(titles, persons, publico_urls_in_arquivo, gold_urls):
    relationships = []
    articles = []

    for title in titles:

        if is_discardable(title):
            continue

        # detect the URL source
        url_type = detect_source_from_url(title)

        # if the URL is part of the golden-data discard it, it will already be in the Graph
        if is_in_gold_data(title, url_type, gold_urls):
            continue

        #  if it's a publico.pt and is in arquivo.pt, discard, and keep the arquivo.pt version
        if url_type == "publico":
            if title["url"] in publico_urls_in_arquivo:
                continue

        # select the highest scoring relationship
        scores = [(k, v) for k, v in title["scores"].items()]
        rel_type = sorted(scores, key=lambda x: x[1], reverse=True)[0]
        person_1 = title["entities"][0]
        person_2 = title["entities"][1]
        news_title = title["title"].strip()

        try:
            crawled_date = extract_date(title["date"], url_type)
        except ValueError as e:
            print(e)
            continue

        p1_id = title["ent_1"]["wiki_id"]
        p1_name = person_1
        build_person(p1_id, p1_name, persons)

        p2_id = title["ent_2"]["wiki_id"]
        p2_name = person_2
        build_person(p2_id, p2_name, persons)

        relationships.append(
            Relationship(
                url=title["url"],
                rel_type=rel_type[0],
                rel_score=rel_type[1],
                ent1=p1_id,
                ent2=p2_id,
                ent1_str=person_1,
                ent2_str=person_2,
            )
        )

        articles.append(
            Article(
                url=title["url"],
                title=news_title,
                source=None,
                date=None,
                crawled_date=crawled_date,
            )
        )

    return articles, persons, relationships


def process_gold(titles):
    persons = defaultdict(Person)
    relationships = []
    articles = []
    urls_to_ignore = []

    def normalize_url(original_url):
        """ makes all publico.pt URLs look like: https://publico.pt/<id>"""
        normalised_url = original_url
        if "www.publico.pt" in original_url and "arquivo.pt" not in original_url:
            normalised_url = original_url.replace("www.publico.pt", "publico.pt")
        if normalised_url.startswith("http://publico.pt"):
            normalised_url = make_https(normalised_url)
        return normalised_url

    for entry in titles:

        if entry["ent1_id"] == "None" or entry["ent2_id"] == "None":
            continue

        normalized_url = normalize_url(entry["url"])  # normalize all publico.pt URLs

        if entry["label"] == "other":
            # add 'other' URLS be skipped if they appear in the extracted data
            urls_to_ignore.append(normalized_url)

        # only index support/opposition relationships, discard all other types of rel_types
        if entry["label"] not in [
            "ent1_supports_ent2",
            "ent2_supports_ent1",
            "ent2_opposes_ent1",
            "ent1_opposes_ent2",
        ]:
            continue

        ent1_id = entry["ent1_id"].split("/")[-1]
        ent2_id = entry["ent2_id"].split("/")[-1]
        build_person(ent1_id, entry["ent1"], persons)
        build_person(ent2_id, entry["ent2"], persons)

        relationships.append(
            Relationship(
                url=normalized_url,
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
                url=normalized_url,
                title=entry["title"],
                source=None,
                date=None,
                crawled_date=entry["date"],
            )
        )

    return articles, persons, relationships, urls_to_ignore


def populate_graph(articles, persons, relationships):
    """
    Adds triples to an RDF graph with the following structure:

        Person triples, we store only the wikidata id and the surface string(s) by which is referred
        to in the news articles;
            <wiki_URI, SKOS.altLabel, name>

        Article triples:
            <url, DC.title, title>
            <url, DC.data, date)

        Relationships as Blank Node:
            - <_rel, ns1.type, rel_type>
            - <_rel, ns1.score, rel_score>
            - <_rel, ns1.url, url>
            - g.add((_rel, ns1.ent1, URIRef(f"http://www.wikidata.org/entity/{rel.ent1}")))
            - g.add((_rel, ns1.ent2, URIRef(f"http://www.wikidata.org/entity/{rel.ent2}")))
            - g.add((_rel, ns1.ent1_str, Literal(rel.ent1_str)))
            - g.add((_rel, ns1.ent2_str, Literal(rel.ent2_str)))

    NOTE: linked-data vocabularies can be seen here: https://lov.linkeddata.es/dataset/lov/
    """
    g = Graph()
    ns1 = Namespace("http://www.politiquices.pt/")
    g.bind("politiquices", ns1)
    wiki_prop = Namespace("http://www.wikidata.org/prop/direct/")
    wiki_item = Namespace("http://www.wikidata.org/entity/")
    g.bind("wd", wiki_item)
    g.bind("wdt", wiki_prop)

    print("\nadding Persons")
    for wikidata_id, person in persons.items():

        # state that in 'politiquices' this is a human, following the same as wikidata.org
        g.add(
            (URIRef(f"http://www.wikidata.org/entity/{wikidata_id}"), wiki_prop.P31, wiki_item.Q5)
        )
        for name in person.known_as:
            g.add(
                (
                    URIRef(f"http://www.wikidata.org/entity/{wikidata_id}"),
                    SKOS.altLabel,
                    Literal(name, lang="pt"),
                )
            )

    print("adding Articles")
    for article in articles:
        g.add((URIRef(article.url), DC.title, Literal(article.title, lang="pt")))
        g.add((URIRef(article.url), DC.date, Literal(article.crawled_date, datatype=XSD.date)))

    print("adding Relationships")
    for rel in relationships:
        _rel = BNode()
        g.add((_rel, ns1.type, Literal(rel.rel_type)))
        g.add((_rel, ns1.score, Literal(rel.rel_score, datatype=XSD.float)))
        g.add((_rel, ns1.url, URIRef(rel.url)))
        g.add((_rel, ns1.ent1, URIRef(f"http://www.wikidata.org/entity/{rel.ent1}")))
        g.add((_rel, ns1.ent2, URIRef(f"http://www.wikidata.org/entity/{rel.ent2}")))
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
    print()


def main():
    args = parse_args()
    arquivo = []
    publico = []
    chave = []
    rels_gold = []
    arquivo_publico_urls = []
    gold_articles = []
    gold_urls = None
    gold_persons = None

    if args.annotations:
        training_data = read_ground_truth("../classifiers/politiquices_data_v1.0.csv")
        gold_articles, gold_persons, rels_gold, urls_to_ignore = process_gold(training_data)
        print("ground truth : ", len(gold_articles))
        gold_urls = [article.url for article in gold_articles] + urls_to_ignore

    if args.arquivo:
        # remove duplicates: keep only unique urls
        arquivo_unique_url = remove_duplicates_with_same_url(args.arquivo)

        # remove duplicates: same crawled url but different crawl date, keep oldest version
        unique = remove_url_crawled_diff_dates_duplicates(arquivo_unique_url)

        # remove duplicates: title + crawl date same and URL overlaps, e.g.: with/without params
        arquivo = remove_duplicates_same_domain(unique)

        # gather all publico.pt URLs
        arquivo_publico_urls = get_publico_urls_in_arquivo(unique)
        print("arquivo.pt   : ", len(arquivo))

    if args.publico:
        publico = remove_duplicates_with_same_url(args.publico)
        print("publico.pt   : ", len(publico))

    if args.chave:
        chave = [entry for entry in processed_titles(args.chave)]
        print("CHAVE        : ", len(chave))

    articles, persons, relationships = process_data(
        arquivo + publico + chave,
        persons=gold_persons,
        publico_urls_in_arquivo=arquivo_publico_urls,
        gold_urls=gold_urls,
    )

    populate_graph(articles + gold_articles, persons, relationships + rels_gold)


if __name__ == "__main__":
    main()
