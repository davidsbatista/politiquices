import csv
import sys
from collections import defaultdict

from jsonlines import jsonlines
from rdflib import Graph
from rdflib import BNode, URIRef, Literal, Namespace, XSD, SKOS
from rdflib.namespace import DC, RDFS

from classes import Person, Article, Relationship


def read_csv_data(file_name):
    with open(file_name, "rt") as f_in:
        tsv_reader = csv.reader(f_in, delimiter="\t")
        classified_titles = [row for row in tsv_reader]
    return classified_titles


def processed_titles(filename):
    with jsonlines.open(filename, mode="r") as reader:
        for line in reader:
            yield line


def extract_date(crawled_date: str):
    year = crawled_date[0:4]
    month = crawled_date[4:6]
    day = crawled_date[6:8]
    hour = crawled_date[8:10]
    minute = crawled_date[10:12]
    second = crawled_date[12:14]
    date_str = f'{year}-{month}-{day}T{hour}:{minute}:{second}'
    # date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    return date_str


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


def process_classified_titles():
    """

    :return:
    """
    persons = defaultdict(Person)
    relationships = []
    articles = []
    seen_hashes = set()
    print("Processing classified titles")
    count = 0
    with jsonlines.open('logs/non_relevant.jsonl', 'w') as non_relevant_writer, \
            jsonlines.open('logs/no_entities.jsonl', 'w') as no_entities_writer, \
            jsonlines.open('logs/no_wiki.jsonl', 'w') as no_wiki__writer:

        for processed_title in processed_titles(sys.argv[1]):

            count += 1

            if count % 25000 == 0:
                print(".", end="", flush=True)

            if processed_title["hash"] in seen_hashes:
                continue

            # non-relevant news articles
            if processed_title["relevancy"]["relevant"] < 0.5:
                non_relevant_writer.write(processed_title)
                continue

            # relevant news articles but without entities
            if "not enough entities" in processed_title["relationship"].keys():
                no_entities_writer.write(processed_title)
                continue

            rel = processed_title["relationship"]
            # recognized entities not linked to Wikidata
            if not rel["entity_1_wiki"] or not rel["entity_2_wiki"]:
                no_wiki__writer.write(processed_title)
                continue

            # ToDo: one can also use a similarity metric
            seen_hashes.add(processed_title["hash"])

            scores = [(k, v) for k, v in rel.items() if isinstance(v, float)]
            rel_type = sorted(scores, key=lambda x: x[1], reverse=True)[0]

            e1_wiki = rel["entity_1_wiki"]['wiki']
            e2_wiki = rel["entity_2_wiki"]['wiki']
            person_1 = processed_title["relationship"]["entity_1"]
            person_2 = processed_title["relationship"]["entity_2"]
            title_cleaned = processed_title["cleaned_title"]
            url = processed_title["entry"]["linkToArchive"]
            crawled_date = extract_date(processed_title['entry']["tstamp"])

            p1_id = e1_wiki
            p1_name = person_1
            build_person(p1_id, p1_name, persons)

            p2_id = e2_wiki
            p2_name = person_2
            build_person(p2_id, p2_name, persons)

            relationships.append(
                Relationship(
                    url=url, rel_type=rel_type[0], rel_score=rel_type[1], ent1=p1_id, ent2=p2_id
                )
            )

            articles.append(
                Article(url=url, title=title_cleaned, source=None, date=None, crawled_date=crawled_date)
            )

        return articles, persons, relationships


def main():
    articles, persons, relationships = process_classified_titles()

    g = Graph()
    ns1 = Namespace("http://some.namespace/with/name#")
    g.bind("my_prefix", ns1)
    wiki_prop = Namespace("http://www.wikidata.org/prop/direct/")
    wiki_item = Namespace("http://www.wikidata.org/entity/")
    g.bind("wd", wiki_item)
    g.bind("wdt", wiki_prop)

    # linked-data vocabularies
    # https://lov.linkeddata.es/dataset/lov/

    print("\nadding Persons")
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
        g.add((URIRef(article.url), DC.date, Literal(article.crawled_date, datatype=XSD.dateTime)))

    print("adding Relationships")
    # add relationships as Blank Node:
    for rel in relationships:
        _rel = BNode()
        g.add((_rel, ns1.type, Literal(rel.rel_type)))
        g.add((_rel, ns1.score, Literal(rel.rel_score, datatype=XSD.float)))
        g.add((_rel, ns1.score, Literal(1.0, datatype=XSD.float)))
        g.add((_rel, ns1.arquivo, URIRef(rel.url)))
        g.add((_rel, ns1.ent1, URIRef(f"http://www.wikidata.org/entity/{rel.ent1}")))
        g.add((_rel, ns1.ent2, URIRef(f"http://www.wikidata.org/entity/{rel.ent2}")))

    # print out the entire Graph in the RDF Turtle format
    # "xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig" and "nquads" are built in.
    print(g.serialize(format="turtle").decode("utf-8"))
    g.serialize(destination="sample.ttl", format="turtle")
    print("graph has {} statements.".format(len(g)))

    print("persons      : ", len(persons))
    print("articles     : ", len(articles))
    print("relationships: ", len(relationships))


if __name__ == "__main__":
    main()
