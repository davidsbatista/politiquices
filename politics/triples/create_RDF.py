import csv
import sys
from collections import defaultdict

from rdflib import Graph
from rdflib import BNode, URIRef, Literal, Namespace, XSD, SKOS
from rdflib.namespace import DC, RDFS

from classes import Person, Article, Relationship


def read_csv_data(file_name):
    with open(file_name, "rt") as f_in:
        tsv_reader = csv.reader(f_in, delimiter="\t")
        classified_titles = [row for row in tsv_reader]
    return classified_titles


def build_person(wikidata_id, name, persons):
    if wikidata_id in persons:
        if name != persons[wikidata_id].name:
            persons[wikidata_id].also_known_as.add(name)
    else:
        persons[wikidata_id] = Person(
            name=name, also_known_as=set(), power_id="", wikidata_id=wikidata_id
        )


def main():
    classified_titles = read_csv_data(sys.argv[1])
    g = Graph()

    ns1 = Namespace("http://some.namespace/with/name#")
    g.bind("my_prefix", ns1)
    wiki_prop = Namespace("http://www.wikidata.org/prop/direct/")
    wiki_item = Namespace("http://www.wikidata.org/entity/")
    g.bind("wd", wiki_item)
    g.bind("wdt", wiki_prop)

    # linked-data vocabularies
    # https://lov.linkeddata.es/dataset/lov/

    persons = defaultdict(Person)
    relationships = []
    articles = []

    for title in classified_titles:

        if "wikidata" in title[7] and "wikidata" in title[8]:
            p1_id = title[7].split("/")[-1]
            p1_name = title[5]
            build_person(p1_id, p1_name, persons)

            p2_id = title[8].split("/")[-1]
            p2_name = title[6]
            build_person(p2_id, p2_name, persons)

            relationships.append(
                Relationship(
                    url=title[4], rel_type=title[1], rel_score=title[2], ent1=p1_id, ent2=p2_id
                )
            )

            articles.append(
                Article(url=title[4], title=title[0], source=None, date=title[3], crawled_date=None)
            )

        else:
            # ToDo: output in a structured way entities not in wikidata
            pass

        continue

    # add all Persons with
    for wikidata_id, person in persons.items():
        g.add(
            (
                URIRef(f"http://www.wikidata.org/entity/{wikidata_id}"),
                SKOS.prefLabel,
                Literal(person.name, lang="pt"),
            )
        )

        # ToDo: distinguir business/political party/person
        # http://www.wikidata.org/wiki/Property:P31     # instance of:
        #
        # https://www.wikidata.org/wiki/Q4830453        # business
        # https://www.wikidata.org/wiki/Q7278           # political party
        # https://www.wikidata.org/wiki/Q5              # human

        g.add(
            (
                URIRef(f"http://www.wikidata.org/entity/{wikidata_id}"),
                wiki_prop.P31,
                wiki_item.Q5
            )
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

    # add all Articles
    for article in articles:
        g.add((URIRef(article.url), DC.title, Literal(article.title, lang="pt")))
        g.add((URIRef(article.url), DC.date, Literal(article.date, datatype=XSD.datetime)))

    for rel in relationships:
        if rel.rel_type == '':
            continue

        _rel = BNode()
        g.add((_rel, ns1.type, Literal(rel.rel_type)))
        # g.add((_rel, ns1.score, Literal(rel.rel_score, datatype=XSD.float)))
        g.add((_rel, ns1.score, Literal(1.0, datatype=XSD.float)))
        g.add((_rel, ns1.arquivo, URIRef(rel.url)))
        g.add((_rel, ns1.ent1, URIRef(f'http://www.wikidata.org/entity/{rel.ent1}')))
        g.add((_rel, ns1.ent2, URIRef(f'http://www.wikidata.org/entity/{rel.ent2}')))

    # print out the entire Graph in the RDF Turtle format
    # "xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig" and "nquads" are built in.
    print(g.serialize(format="turtle").decode("utf-8"))
    g.serialize(destination="sample.ttl", format="turtle")
    print("graph has {} statements.".format(len(g)))
    sys.exit()

    # Titles and dates of all articles where the classification is 'ent1_supports_ent2' and 'ent2'
    # is Sócrates(Q182367)


if __name__ == "__main__":
    main()
