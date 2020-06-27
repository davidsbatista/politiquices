import json
import os
import sys
import logging
from collections import defaultdict

import joblib
from SPARQLWrapper import SPARQLWrapper, JSON

from flask import request, jsonify
from flask import render_template
from app import app

from datetime import datetime
import pt_core_news_sm

nlp = pt_core_news_sm.load()

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, 'models/')

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

clf = joblib.load(MODELS + 'relationship_clf.joblib')
vectorizer = joblib.load(MODELS + 'vectorizer.joblib')
le = joblib.load(MODELS + 'label_encoder.joblib')

# utils


def convert_dates(date: str):
    date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime('%Y %b')


# web interface

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

    items = {'image': image_url,
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
    with open('front-end/entities_in_database.json', 'rt') as f_in:
        entities = json.load(f_in)
    persons = set()
    items = []
    for e in entities['results']['bindings']:
        url = e['person']['value']
        if url in persons:
            continue
        persons.add(url)
        name = e['personLabel']['value']
        if 'image_url' in e:
            image_url = e['image_url']['value']
        else:
            image_url = "/static/images/no_picture.jpg"
        items.append({'wikidata_url': url,
                      'wikidata_id': url.split('/')[-1],
                      'name': name,
                      'image_url': image_url})

    return render_template('all_entities.html', items=items)


# http-end-points

@app.route('/sentence')
def sentence():
    return render_template('input_sentence.html')


@app.route('/sentence_result', methods=['POST'])
def sentence_result():
    if request.method == 'POST':
        data = request.form
        sent = data['sentence']
        ent_per = named_entity(sent)
        clf_result = sentence_classifier(sent)
        person_mappings = defaultdict(list)
        for per in ent_per:
            items = []
            print(f'querying: {per}')
            wiki_results = query_wikidata(per)
            for row in wiki_results['results']['bindings']:
                url = row['subj']['value']
                name = row['subjLabel']['value']
                party = ''
                if 'political_partyLabel' in row:
                    party = row['political_partyLabel']['value']
                items.append({'name': name, 'url': url, 'party': party})
            person_mappings[per] = items

        result = {'sentence': sent,
                  'relationship_clf': clf_result, 'named_entities': ent_per,
                  "wikidata_mappings": person_mappings}

        return jsonify(result)
        # return render_template('list_sent_clf_results.html', items=result)


@app.route('/wikidata')
def wikidata():
    return render_template('input_wikidata.html')


@app.route('/wikidata_result', methods=['POST'])
def wikidata_result():
    items = []
    if request.method == 'POST':
        data = request.form
        results = query_wikidata(data['entity'])
        for row in results['results']['bindings']:
            url = row['subj']['value']
            name = row['subjLabel']['value']
            party = ''
            if 'political_partyLabel' in row:
                party = row['political_partyLabel']['value']
            items.append({'name': name, 'url': url, 'party': party})

        if data['type'] == 'JSON':
            return jsonify(items)

        if items:
            return render_template('list_entities.html', items=items)
        else:
            return render_template('list_entities.html')


def query_sparql(query, endpoint):
    if endpoint == 'wiki':
        endpoint_url = "https://query.wikidata.org/sparql"
    elif endpoint == 'local':
        endpoint_url = "http://localhost:3030/arquivo/query"
    else:
        print("endpoint not valid")
        return None

    # TODO adjust user agent; see https://w.wiki/CX6
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results


def query_wikidata(entity_name):
    # NOTE: you need to double the {{ and }} to allow string.format to work

    # ToDo:
    #  - add Madeira and Azores politicians
    #  - add anyone that was/is member of portuguese political party
    #  - add anyone that was/is member of portuguese public institutions, e.g.: CGD, Banco Portugal
    #  - Zeinal Bava

    """
    SELECT DISTINCT ?subj ?subjLabel
    WHERE {
      { ?subj wdt:P39 wd:Q19953703.
        ?subj rdfs:label ?subjLabel.}  # membros do parlamento continental
      UNION
      { ?subj wdt:P39 wd:Q1101237.
        ?subj rdfs:label ?subjLabel.}   # membros do governo regional ?
      FILTER(LANG(?subjLabel) = "pt")
    } ORDER BY ?subjLabel

    """

    entity_name_parts = entity_name.split()
    entity_name_regex = '.*' + '.*'.join(entity_name_parts) + '.*'
    endpoint_url = "https://query.wikidata.org/sparql"

    query = """SELECT ?subj ?image_url ?subjLabel ?official_nameLabel ?birth_nameLabel ?political_partyLabel
    WHERE
    {{
      ?subj wdt:P39 wd:Q19953703.
      ?subj rdfs:label ?subjLabel.

      OPTIONAL {{ ?subj wdt:P102 ?political_party. }}
      OPTIONAL {{ ?subj wdt:P1448 ?official_name. }}

      FILTER(LANG(?subjLabel) = "pt")
      FILTER regex(?subjLabel, "{entity_regex}", "i" )

      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],pt". }}
    }} ORDER BY ?subjLabel
    """.format(entity_regex=entity_name_regex)

    print("querying for entity: ", entity_name)
    print("\n" + query + "\n")

    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    return sparql.query().convert()


def expand_contractions(title):
    """
    see: https://blogs.transparent.com/portuguese/contractions-in-portuguese/

    :param title:
    :return:
    """

    # 01. Em
    title = title.replace(" no ", " em o ")
    title = title.replace(" na ", " em a ")
    title = title.replace(" nos ", " em os ")
    title = title.replace(" nas ", " em as ")
    title = title.replace(" num ", " em um ")
    title = title.replace(" numa ", " em uma ")
    title = title.replace(" nuns ", " em uns ")
    title = title.replace(" numas ", " em umas ")

    # 02. De
    title = title.replace(" do ", " de o ")
    title = title.replace(" da ", " de a ")
    title = title.replace(" dos ", " de os ")
    title = title.replace(" das ", " de as ")

    title = title.replace(" dum ", " de um ")
    title = title.replace(" duma ", " de uma ")
    title = title.replace(" duns ", " de uns ")
    title = title.replace(" dumas", " de umas ")

    title = title.replace(" deste ", " de este ")
    title = title.replace(" desta ", " de esta ")
    title = title.replace(" destes ", " de estes ")
    title = title.replace(" destas", " de estas ")

    title = title.replace(" desse ", " de esse ")
    title = title.replace(" dessa ", " de essa ")
    title = title.replace(" desses ", " de esses ")
    title = title.replace(" dessas ", " dessas ")

    # 03. Por
    title = title.replace(" pelo ", " por o ")
    title = title.replace(" pela ", " por a ")
    title = title.replace(" pelos ", " por os ")
    title = title.replace(" pelas", " por as ")

    # ToDo: can be two possibilities
    """
    por + os / por + eles = pelos
    por + as / por + elas = pelas
    """

    # 04. A
    title = title.replace(" ao ", " a o ")
    title = title.replace(" à ", " a a ")
    title = title.replace(" aos ", " a os ")
    title = title.replace(" às ", " a as ")

    return title


def named_entity(sentence):
    title = expand_contractions(sentence)
    doc = nlp(title)
    ent_per = [ent.text for ent in doc.ents if str(ent.label_) == 'PER']
    return ent_per


def sentence_classifier(sentence):
    predicted_probs = clf.predict_proba(vectorizer.transform([sentence]))
    results = []
    for idx, label in enumerate(le.classes_):
        results.append({'label': label, 'score': predicted_probs[0][idx]})
    return results
