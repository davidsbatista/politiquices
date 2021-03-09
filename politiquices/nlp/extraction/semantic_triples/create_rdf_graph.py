import re
import argparse
import operator
from collections import defaultdict
from datetime import datetime

from classes import Article, Person, Relationship
from itertools import groupby
from jsonlines import jsonlines
from rdflib import BNode, Graph, Literal, Namespace, SKOS, URIRef, XSD
from rdflib.namespace import DC, RDFS

publico_pt_urls = ['http://economia.publico.pt/',
                   'http://publico.pt/',
                   'http://www.publico.pt/',
                   'https://economia.publico.pt/',
                   'https://publico.pt/',
                   'https://www.publico.pt/']


def remove_duplicates_with_same_url(f_name):
    """
    discard duplicate URLs
    """
    seen = set()
    unique = []
    duplicate = 0
    for entry in processed_titles(f_name):
        if any(entry['url'].startswith(x) for x in publico_pt_urls):
            url = minimize_publico_urls(entry['url'])
        else:
            url = entry['url']

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
                'title': earliest[1],
                'date': earliest[2],
                'url': earliest[3],
                'entities': earliest[4],
                'ent_1': earliest[5],
                'ent_2': earliest[6],
                'scores': earliest[7]
            }
        else:
            article = articles[0]
            result = {
                'title': article[1],
                'date': article[2],
                'url': article[3],
                'entities': article[4],
                'ent_1': article[5],
                'ent_2': article[6],
                'scores': article[7]
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
            'title': earliest[1],
            'date': earliest[2],
            'url': earliest[3],
            'entities': earliest[4],
            'ent_1': earliest[5],
            'ent_2': earliest[6],
            'scores': earliest[7]
        }
        articles_unique.append(result)

    print(f'{len(articles_unique)} unique articles')

    return articles_unique


def processed_titles(filename):
    with jsonlines.open(filename, mode="r") as reader:
        for line in reader:
            yield line


def extract_date(crawled_date: str, url_type):

    if url_type == 'publico':
        try:
            date_obj = datetime.strptime(crawled_date, "%Y-%m-%d %H:%M:%S")
            return datetime.strftime(date_obj, '%Y-%m-%d')
        except ValueError as e:
            raise e

    elif url_type == 'chave':
        date_obj = datetime.strptime(crawled_date, "%Y-%m-%d")
        return datetime.strftime(date_obj, '%Y-%m-%d')
        pass

    else:
        year = crawled_date[0:4]
        month = crawled_date[4:6]
        day = crawled_date[6:8]
        hour = crawled_date[8:10]
        minute = crawled_date[10:12]
        second = crawled_date[12:14]
        date_str = f"{year}-{month}-{day}T{hour}:{minute}:{second}"

        if int(year) > 2020:
            raise ValueError(date_str)
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
            return datetime.strftime(date_obj, '%Y-%m-%d')
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


def process_classified_titles(titles):
    persons = defaultdict(Person)
    relationships = []
    articles = []

    for title in titles:
        e1_wiki = title["ent_1"]["wiki"]
        e2_wiki = title["ent_2"]["wiki"]
        scores = [(k, v) for k, v in title["scores"].items()]
        rel_type = sorted(scores, key=lambda x: x[1], reverse=True)[0]
        person_1 = title["entities"][0]
        person_2 = title["entities"][1]
        news_title = title["title"].strip()
        url = title["url"]

        # ignore empty URLs
        if url == 'None' or url == '\\N':
            continue

        # try to detect article origin
        url_type = 'arquivo'
        if any(url.startswith(x) for x in publico_pt_urls):
            url_type = 'publico'
        elif url.startswith('https://www.linguateca.pt/CHAVE?'):
            url_type = 'chave'

        # special case to transform publico.pt urls to: http://publico.pt/<news_id>
        if url_type == 'publico':
            url = minimize_publico_urls(url)
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


def minimize_publico_urls(url):
    news_id = url.split("-")[-1].replace('?all=1', '')
    if not re.match(r'^[0-9]+$', news_id):
        news_id_ = news_id.split("_")[-1]
        news_id = news_id_.replace(".1", '')
    if not re.match(r'^[0-9]+$', news_id):
        raise ValueError("invalid publico.pt id: ", news_id)
    url = 'http://publico.pt/' + news_id
    return url


def populate_graph(articles, persons, relationships, args):
    g = Graph()

    ns1 = Namespace("http://www.politiquices.pt/")
    g.bind("politiquices", ns1)

    wiki_prop = Namespace("http://www.wikidata.org/prop/direct/")
    wiki_item = Namespace("http://www.wikidata.org/entity/")
    g.bind("wd", wiki_item)
    g.bind("wdt", wiki_prop)

    # linked-data vocabularies
    # https://lov.linkeddata.es/dataset/lov/

    print("adding Persons")
    # add Person triples: <wiki_URI, SKOS.prefLabel, name>
    for wikidata_id, person in persons.items():

        # ToDo: make sure pref name is at least two names: first + surname
        g.add(
            (
                URIRef(f"http://www.wikidata.org/entity/{wikidata_id}"),
                SKOS.prefLabel,
                Literal(person.name, lang="pt"),
            )
        )

        # is this needed? probably to match with wikidata graph?
        # http://www.wikidata.org/wiki/Property:P31     # instance of:
        # https://www.wikidata.org/wiki/Q5              # human
        # to filter in the queries to get only persons and not articles or relationships
        g.add(
            (URIRef(f"http://www.wikidata.org/entity/{wikidata_id}"), wiki_prop.P31, wiki_item.Q5)
        )

        g.add(
            (
                URIRef(f"http://www.wikidata.org/entity/{wikidata_id}"),
                RDFS.label,
                Literal(person.name, lang="pt"),
            )
        )

        for alt_name in person.also_known_as:
            g.add(
                (
                    URIRef(f"http://www.wikidata.org/entity/{wikidata_id}"),
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

        # ToDo: set score to 1.0 when indexing annotated data
        # g.add((_rel, ns1.score, Literal(1.0, datatype=XSD.float)))

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


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publico", help="input JSONL file with publico.pt results")
    parser.add_argument("--arquivo", help="input JSONL file with arquivo.pt results")
    parser.add_argument("--chave", help="input JSONL file with CHAVE results")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    arquivo_articles = []
    publico_articles = []
    chave_articles = []

    if args.arquivo:
        print("Processing arquivo.pt articles")
        # remove duplicates: keep only unique urls
        arquivo_unique_url = remove_duplicates_with_same_url(args.arquivo)

        # remove duplicates on same crawled url but different crawl date, keep oldest version
        unique = remove_url_crawled_diff_dates_duplicates(arquivo_unique_url)

        # remove duplicates: (i.e., title + crawl date same, one url is sub-domain of other)
        # ToDo: check it this still happens
        arquivo_articles = remove_duplicates_same_domain(unique)

    if args.publico:
        print("\nProcessing publico.pt articles")
        publico_articles = remove_duplicates_with_same_url(args.publico)

    if args.chave:
        print("\nProcessing CHAVE articles")
        chave_articles = [entry for entry in processed_titles(args.chave)]

    print("\nArticles after duplicate cleaning")
    print("arquivo.pt: ", len(arquivo_articles))
    print("publico.pt: ", len(publico_articles))
    print("CHAVE     :   ", len(chave_articles))

    all_articles = []
    for article in arquivo_articles+publico_articles+chave_articles:
        if article['ent_1']['wiki'] == article['ent_2']['wiki']:
            continue
        all_articles.append(article)

    print()
    articles, persons, relationships = process_classified_titles(all_articles)
    populate_graph(articles, persons, relationships, args)


if __name__ == "__main__":
    main()
