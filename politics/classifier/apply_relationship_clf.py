import csv
import json
import os
import sys
from functools import lru_cache, reduce
from random import randint
from time import sleep

import joblib
import numpy as np
import pt_core_news_sm
import requests
from keras.models import load_model
from keras_preprocessing.sequence import pad_sequences

from politics.utils import clean_sentence

MODELS = "trained_models/"

nlp = pt_core_news_sm.load(disable=["tagger", "parser"])


def load_sentences(filename):
    with open(filename, "rt") as f_in:
        tsv_reader = csv.reader(f_in, delimiter="\t")
        titles = [row for row in tsv_reader]
    return titles


def load_models():
    clf = load_model(MODELS + "rel_clf_2020-07-04-00:07:51.h5")
    word2index = joblib.load(MODELS + "word2index_2020-07-04-00:07:51.joblib")
    le = joblib.load(MODELS + "label_encoder_2020-07-04-00:07:51.joblib")
    with open(MODELS + "max_input_length", "rt") as f_in:
        max_input_length = int(f_in.read().strip())

    return clf, le, word2index, max_input_length


def filter_sentences_persons(titles):
    # filter only the ones with at least two 'PER'
    # ToDo: add also 'PER' from a hand-crafted list,
    #  see: https://spacy.io/usage/rule-based-matching

    wrong_PER = load_wrong_per()
    print(f"Extracting named-entities from {len(titles)} titles")
    titles_doc = [(t[0], nlp(t[1]), t[2]) for t in titles]
    titles_per = []
    for title in titles_doc:
        persons = [ent.text for ent in title[1].ents if ent.label_ == "PER"]
        if len(persons) == 2:
            if not set(persons).intersection(set(wrong_PER)):
                titles_per.append((title, persons))

    return titles_per


def classify_sentences(per_titles, word2index, max_input_length, clf, le):

    # ToDo: if no context or context = 1 char return None

    # replace entity name by 'PER'
    docs = [d[0][1].text.replace(d[1][0], "PER").replace(d[1][1], "PER") for d in per_titles]

    word_no_vectors = set()
    all_sent_tokens = []
    for doc in docs:
        all_sent_tokens.append([str(t).lower() for t in doc])
    x_vec = []
    for sent in all_sent_tokens:
        tokens_idx = []
        for tok in sent:
            if tok in word2index:
                tokens_idx.append(word2index[tok])
            else:
                tokens_idx.append(word2index["UNKNOWN"])
                word_no_vectors.add(tok)
        x_vec.append(tokens_idx)

    print("words without vector: ", len(word_no_vectors))

    x_vec_padded = pad_sequences(x_vec, maxlen=max_input_length, padding="post", truncating="post")

    predicted_probs = clf.predict(x_vec_padded)
    labels_idx = np.argmax(predicted_probs, axis=1)
    pred_labels = le.inverse_transform(labels_idx)

    return pred_labels, predicted_probs


def main():
    clf, le, word2index, max_input_length = load_models()
    sentences = load_sentences(sys.argv[0])

    # ToDo: merge in one function
    titles = [(s[0], clean_sentence(s[1]).strip().strip("\u200b"), s[2]) for s in sentences]
    titles_persons = filter_sentences_persons(titles)

    pred_labels, predicted_probs = classify_sentences(
        titles_persons, word2index, max_input_length, clf, le
    )

    for label, sentence, prob in zip(pred_labels, titles_persons, predicted_probs):
        idx_max = np.argmax(prob)
        if prob[idx_max] > 0.9:
            print(label, prob, '\t', sentence[1], sentence[0][1])

    # ToDo: analyze/ dump results
    """
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
                if str(ent.label_) == "PER":

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
                        ent1_wiki = wiki_id[0]["url"]

                if idx == 1:
                    ent2 = ent
                    if len(wiki_id) == 1:
                        ent2_wiki = wiki_id[0]["url"]

            row = [
                sentence,
                pred_class,
                pred_class_score,
                date,
                original_url,
                ent1,
                ent2,
                ent1_wiki,
                ent2_wiki,
                title[1].ents,
            ]

            print(idx_titles, "\t", sentence)
            print(pred_class)
            print()
            all_results.append(row)
    with open("all_results.tsv", "wt") as f_out:
        tsv_writer = csv.writer(f_out, delimiter="\t")
        for row in all_results:
            tsv_writer.writerow(row)

    with open("entities_mappings.json", "wt") as f_out:
        json.dump(my_cache, f_out)

    print(query_wikidata.cache_info())
    """


if __name__ == "__main__":
    main()
