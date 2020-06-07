import csv
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from rdflib import Graph
from rdflib import BNode, URIRef, Literal, Namespace, RDF, XSD
from rdflib.namespace import FOAF, DC


@dataclass
class Person:
    name: str
    power_id: str
    wikidata_id: str


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
    sentence: str
    url: str
    date: datetime
    rel_type: str
    rel_score: float
    ent1: Person
    ent2: Person


def read_csv_data(file_name):
    with open(file_name, 'rt') as f_in:
        tsv_reader = csv.reader(f_in, delimiter='\t')
        classified_titles = [row for row in tsv_reader]
    return classified_titles


def main():
    classified_titles = read_csv_data(sys.argv[1])
    g = Graph()

    ns1 = Namespace('http://some.namespace/with/name#')
    g.bind('my_prefix', ns1)
    wiki_prop = Namespace("http://www.wikidata.org/prop/direct/")
    wiki_item = Namespace('http://www.wikidata.org/entity/')
    g.bind('wd', wiki_item)
    g.bind('wdt', wiki_prop)

    # linked-data vocabularies
    # https://lov.linkeddata.es/dataset/lov/

    for title in classified_titles:
        if title[7] and title[8]:

            p1 = Person(name=title[5], power_id='', wikidata_id=title[7].split("/")[-1])
            p2 = Person(name=title[6], power_id='', wikidata_id=title[8].split("/")[-1])
            rel = Relationship(sentence=title[0], url=title[4], date=title[3], rel_type=title[1],
                               rel_score=title[2], ent1=p1, ent2=p2)

            # Create Persons
            # ToDo: set a unique name and a also-known-as
            # see vocabulary in RDF

            g.add((URIRef(f'http://www.wikidata.org/entity/{p1.wikidata_id}'), FOAF.name, Literal(p1.name, lang="pt")))
            g.add((URIRef(f'http://www.wikidata.org/entity/{p2.wikidata_id}'), FOAF.name, Literal(p2.name, lang="pt")))

            # g.add((URIRef(f'http://www.wikidata.org/entity/{p1.wikidata_id}'), FOAF.a, FOAF.Person))
            # g.add((URIRef(f'http://www.wikidata.org/entity/{p2.wikidata_id}'), FOAF.a, FOAF.Person))

            # Create ArquivoPT article
            g.add((URIRef(rel.url), DC.title, Literal(rel.sentence, lang="pt")))
            g.add((URIRef(rel.url), DC.date, Literal(rel.date, datatype=XSD.datetime)))

            # create relationships with: rel_type, score, article, ent1, ent2
            test = BNode()
            ent1 = URIRef(f'http://www.wikidata.org/entity/{p1.wikidata_id}')
            ent2 = URIRef(f'http://www.wikidata.org/entity/{p2.wikidata_id}')

            g.add((test, ns1.label, Literal(rel.rel_type)))
            g.add((test, ns1.score, Literal(rel.rel_score, datatype=XSD.float)))
            g.add((test, ns1.arquivo, URIRef(rel.url)))
            g.add((test, ns1.ent1, ent1))
            g.add((test, ns1.ent2, ent2))

    # print out the entire Graph in the RDF Turtle format
    # "xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig" and "nquads" are built in.
    print(g.serialize(format="turtle").decode("utf-8"))
    g.serialize(destination='sample.ttl', format="turtle")
    print("graph has {} statements.".format(len(g)))
    exit(-1)

    # Titles and dates of all articles where the classification is 'ent1_supports_ent2' and 'ent2'
    # is Sócrates(Q182367)

    qres = g.query(
        """SELECT DISTINCT ?title ?date ?ent1 ?party
           WHERE {
              ?rel my_prefix:label "ent1_supports_ent2" .
              ?rel my_prefix:arquivo ?arquivo .
              ?arquivo ns1:date ?date .
              ?arquivo ns1:title ?title .
              ?rel my_prefix:ent2 wd:Q182367 .
              ?rel my_prefix:ent1 ?ent1 .
           }""")

    # SERVICE <http://www.wikidata.org/wiki/> { ?ent1 wdt:P102 ?party . }

    """
    print(qres)
    print(len(qres))

    for row in qres:
        print(row)
        print(len(row))
    """


if __name__ == '__main__':
    main()
