import json
from functools import lru_cache
import os
import sys
import csv
from random import randint
from time import sleep

import requests
import numpy as np
from functools import reduce

import joblib
import pt_core_news_sm

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(APP_ROOT, '../webapp/app/models/')

nlp = pt_core_news_sm.load()


def clean_sentences(text):

    to_clean = ['Visão |',
                'Expresso |',
                'SIC Notícias |',
                '- Política - PUBLICO.PT',
                ' – Observador', ' – Obser',
                ' - RTP Noticias',
                ' - Renascença',
                ' - Expresso.pt',
                ' - JN',
                ' > TVI24', ' > Política', 'VIDEO -', ' > Geral', ' > TV',
                ' (C/ VIDEO)',
                ' - Opinião - DN',
                'i:',
                'DNOTICIAS.PT',
                ' - Lusa - SA',
                ' | Económico',
                ' - Sol',
                ' | Diário Económico.com',
                ' - PÚBLICO',
                ' – O Jornal Económico', ' – O Jornal Eco', ' – O Jornal',
                'DN Online:', ' - dn - DN', ' - Portugal - DN', ' - Galerias - DN']

    return reduce(lambda a, v: a.replace(v, ''), to_clean, text)


def load_sentences():
    with open(sys.argv[1], 'rt') as f_in:
        tsv_reader = csv.reader(f_in, delimiter='\t')
        titles = [row for row in tsv_reader]
    return titles


@lru_cache(maxsize=5000, typed=False)
def query_wikidata(name):
    url = "http://0.0.0.0:5000/wikidata_result"
    payload = {'entity': name, 'type': 'JSON'}
    response = requests.request("POST", url, data=payload)
    return response.json()


def load_wrong_per():
    with open("wrong_PER.txt", 'rt') as f_in:
        return [line.strip() for line in f_in]


def main():
    clf = joblib.load(MODELS + 'relationship_clf.joblib')
    vectorizer = joblib.load(MODELS + 'vectorizer.joblib')
    le = joblib.load(MODELS + 'label_encoder.joblib')
    sentences = load_sentences()
    wrong_PER = load_wrong_per()

    print(wrong_PER)

    titles = [(s[0], clean_sentences(s[1]).strip().strip(u'\u200b'), s[2]) for s in sentences]

    # filter only the ones with at least two 'PER'
    # ToDo: add also 'PER' from a hand-crafted list,
    #  see: https://spacy.io/usage/rule-based-matching
    print(f'Extracting named-entities from {len(titles)} titles')
    titles_doc = [(t[0], nlp(t[1]), t[2]) for t in titles]
    titles_per = []
    for title in titles_doc:
        persons = [ent.text for ent in title[1].ents if ent.label_ == 'PER']
        if len(persons) == 2:
            if not set(persons).intersection(set(wrong_PER)):
                titles_per.append(title)

    print(len(titles_per))
    titles_vectors = vectorizer.transform([title[1].text for title in titles_per])
    titles_probs = clf.predict_proba(titles_vectors)
    print(titles_vectors.shape)
    print(titles_probs.shape)

    # dump this to file
    my_cache = dict()

    all_results = []

    for idx_titles, (title, probs) in enumerate(zip(titles_per, titles_probs)):
        if np.amax(probs) > 0.5:
            # ToDo: if 'other' skip entity linking
            pred_class = le.classes_[np.argmax(probs)]
            pred_class_score = np.amax(probs)
            sentence = title[1]
            date = title[0]
            original_url = title[2]
            entities = dict()

            for ent in title[1].ents:
                if str(ent.label_) == 'PER':

                    sleep_sec = randint(0, 2)
                    print("sleeping for", sleep_sec, "secs")
                    sleep(sleep_sec)
                    results = query_wikidata(ent.text)

                    my_cache[ent.text] = results
                    entities[ent.text] = results

            ent1 = None
            ent2 = None
            ent1_wiki = None
            ent2_wiki = None

            for idx, (ent, wiki_id) in enumerate(entities.items()):
                if idx == 0:
                    ent1 = ent
                    if len(wiki_id) == 1:
                        ent1_wiki = wiki_id[0]['url']

                if idx == 1:
                    ent2 = ent
                    if len(wiki_id) == 1:
                        ent2_wiki = wiki_id[0]['url']

            row = [sentence, pred_class, pred_class_score, date, original_url,
                   ent1, ent2, ent1_wiki, ent2_wiki, title[1].ents]

            print(idx_titles, '\t', sentence)
            print(pred_class)
            print()
            all_results.append(row)

    with open('all_results.tsv', 'wt') as f_out:
        tsv_writer = csv.writer(f_out, delimiter='\t')
        for row in all_results:
            tsv_writer.writerow(row)

    with open('entities_mappings.json', 'wt') as f_out:
        json.dump(my_cache, f_out)

    print(query_wikidata.cache_info())


if __name__ == '__main__':
    main()
