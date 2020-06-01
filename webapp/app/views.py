import os
import sys
import logging
from collections import defaultdict

import joblib
from SPARQLWrapper import SPARQLWrapper, JSON

from flask import request, jsonify
from flask import render_template
from app import app

import pt_core_news_sm
nlp = pt_core_news_sm.load()


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, 'models/')

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

clf = joblib.load(MODELS+'relationship_clf.joblib')
vectorizer = joblib.load(MODELS+'vectorizer.joblib')
le = joblib.load(MODELS+'label_encoder.joblib')


@app.route('/')
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
    entity_name_regex = '.*'+'.*'.join(entity_name_parts)+'.*'
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
    print("\n"+query+"\n")

    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    return sparql.query().convert()
