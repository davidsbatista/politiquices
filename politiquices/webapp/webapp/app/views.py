import json
import os
import logging
from datetime import datetime

from flask import request
from flask import render_template
from app import app

from politiquices.webapp.webapp.app.sparql_queries import query_sparql
from politiquices.webapp.webapp.app.sparql_queries import initalize


def convert_dates(date: str):
    date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime('%Y %b')


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


@app.route('/entity')
def detail_entity():
    wiki_id = request.args.get('q')
    print(wiki_id)

    # entity info
    query = f"""SELECT DISTINCT ?image_url ?officeLabel ?education ?start ?end
               WHERE {{
                wd:{wiki_id} wdt:P18 ?image_url;
                                 p:P39 ?officeStmnt.
                ?officeStmnt ps:P39 ?office.
                OPTIONAL {{ ?officeStmnt pq:P580 ?start. }}
                OPTIONAL {{ ?officeStmnt pq:P582 ?end. }}
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],pt". }}
                }} ORDER BY ?start"""

    results = query_sparql(query, 'wiki')
    image_url = None
    offices = []
    for e in results['results']['bindings']:
        if not image_url:
            image_url = e['image_url']['value']

        start = None
        end = None
        if 'start' in e:
            start = convert_dates(e['start']['value'])
        if 'end' in e:
            end = convert_dates(e['end']['value'])

        offices.append({'title': e['officeLabel']['value'],
                        'start': start,
                        'end': end})

    query = f"""
        PREFIX       wdt:  <http://www.wikidata.org/prop/direct/>
    PREFIX        wd:  <http://www.wikidata.org/entity/>
    PREFIX        bd:  <http://www.bigdata.com/rdf#>
    PREFIX  wikibase:  <http://wikiba.se/ontology#>
    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX		 ns2: <http://www.w3.org/2004/02/skos/core#>

            SELECT DISTINCT ?rel_type ?arquivo_doc ?title ?ent2 ?ent2_name
               WHERE {{
                ?rel my_prefix:ent1 wd:{wiki_id} .
                ?rel my_prefix:type ?rel_type .
                ?rel my_prefix:ent2 ?ent2 .
                ?ent2 rdfs:label ?ent2_name .
                ?rel my_prefix:arquivo ?arquivo_doc .
                ?arquivo_doc dc:title ?title .
                FILTER (?rel_type != "other")}}
    """
    ent1_results = query_sparql(query, 'local')

    query = f"""
    PREFIX       wdt:  <http://www.wikidata.org/prop/direct/>
    PREFIX        wd:  <http://www.wikidata.org/entity/>
    PREFIX        bd:  <http://www.bigdata.com/rdf#>
    PREFIX  wikibase:  <http://wikiba.se/ontology#>
    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX		 ns2: <http://www.w3.org/2004/02/skos/core#>

            SELECT DISTINCT ?rel_type ?arquivo_doc ?title ?ent1 ?ent1_name
               WHERE {{
                ?rel my_prefix:ent2 wd:{wiki_id} .
                ?rel my_prefix:type ?rel_type .
                ?rel my_prefix:ent1 ?ent1 .
                ?ent1 rdfs:label ?ent1_name .
                ?rel my_prefix:arquivo ?arquivo_doc .
                ?arquivo_doc dc:title ?title .
                FILTER (?rel_type != "other")}}
    """
    ent2_results = query_sparql(query, 'local')

    opposed = []
    supported = []
    for e in ent1_results['results']['bindings']:
        rel = {'url': e['arquivo_doc']['value'],
               'title': e['title']['value'],
               'ent2_url': e['ent2']['value'],
               'ent2_name': e['ent2_name']['value']}

        if e['rel_type']['value'] == "ent1_opposes_ent2":
            opposed.append(rel)
        elif e['rel_type']['value'] == "ent1_supports_ent2":
            supported.append(rel)

    opposed_by = []
    supported_by = []
    for e in ent2_results['results']['bindings']:
        rel = {'url': e['arquivo_doc']['value'],
               'title': e['title']['value'],
               'ent1_url': e['ent1']['value'],
               'ent1_name': e['ent1_name']['value']}

        if e['rel_type']['value'] == "ent1_opposes_ent2":
            opposed_by.append(rel)
        elif e['rel_type']['value'] == "ent1_supports_ent2":
            supported_by.append(rel)

    """
    print(image_url)
    print("")
    print(offices)
    print("")
    print(opposed)
    print("")
    print(supported)
    print("")
    print(opposed_by)
    print("")
    print(supported_by)
    """

    items = {'wiki_id': wiki_id,
             'image': image_url,
             'offices': offices,
             'opposed': opposed,
             'supported': supported,
             'opposed_by': opposed_by,
             'supported_by': supported_by}

    for k, v in items.items():
        print(k, '\t', v)

    return render_template('entity_detail.html', items=items)


@app.route('/')
@app.route('/entities')
def list_entities():
    # ToDo: run this on the Makefile, just after the server is launched
    print("Getting entities")
    entities = query_sparql(initalize(), 'local')
    persons = set()
    items = []

    for e in entities['results']['bindings']:
        url = e['item']['value']
        if url in persons:
            continue
        persons.add(url)
        name = e['label']['value']
        if 'image_url' in e:
            image_url = e['image_url']['value']
        else:
            image_url = "/static/images/no_picture.jpg"
        items.append({'wikidata_url': url,
                      'wikidata_id': url.split('/')[-1],
                      'name': name,
                      'image_url': image_url})

    # with open('all-entities-frontend.json', 'wt') as outfile:
    #     json.dump(items, outfile)

    return render_template('all_entities.html', items=items)


