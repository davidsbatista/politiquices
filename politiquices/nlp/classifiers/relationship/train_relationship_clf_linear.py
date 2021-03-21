import re

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder

from politiquices.nlp.classifiers.relationship.sentiment import WordSentiment
from politiquices.nlp.classifiers.utils.ml_utils import print_cm
from politiquices.nlp.utils.utils import (
    read_ground_truth,
    find_sub_list,
    clean_title_quotes,
    clean_title_re,
)

nlp = spacy.load(
    "pt_core_news_lg",
    disable=["tagger", "parser", "ner", "attribute_ruler"],
)

other_labels = [
        "ent1_asks_support_ent2",
        "ent2_asks_support_ent1",
        "ent1_asks_action_ent2",
        "ent1_replaces_ent2",
        "ent2_replaces_ent1",
        "mutual_disagreement",
        "mutual_agreement",
        "more_entities",
        "meet_together",
        "other",
    ]


def get_context(title_pos_tags, ent1, ent2):
    ent1_tokens = ent1.split()
    ent2_tokens = ent2.split()
    title_text = [t.text for t in title_pos_tags]
    ent1_interval = find_sub_list(ent1_tokens, title_text)
    if ent1_interval:
        ent1_start, ent1_end = ent1_interval
        ent2_interval = find_sub_list(ent2_tokens, title_text)
        if ent2_interval:
            ent2_start, ent2_end = ent2_interval
            return title_pos_tags[ent1_end + 1: ent2_start]


def get_pos_tags(sentence):
    doc = nlp(sentence)
    return [t for t in doc]


def remap_y_target(y_labels):
    return ['other' if y_sample in other_labels else re.sub(r"_?ent[1-2]_?", "", y_sample)
            for y_sample in y_labels]


def get_text_tokens(x_data, tokenized=True):
    textual_context = []
    for x in x_data:
        title = x['title']
        ent1 = x['ent1']
        ent2 = x['ent2']
        pos_tags = get_pos_tags(title)
        context = get_context(pos_tags, ent1, ent2)
        if tokenized:
            context_text = [t.text for t in context]
        else:
            context_text = ' '.join([t.text for t in context])
        textual_context.append(context_text)

    return textual_context


def dummy_fun(doc):
    return doc


def main():
    training_data = read_ground_truth("../../../politiquices_training_data.tsv")
    training_data_webapp = read_ground_truth("../../api_annotations/annotations_from_webapp.tsv")
    all_data = training_data + training_data_webapp
    labels = remap_y_target([s['label'] for s in all_data])
    skf = StratifiedKFold(n_splits=5, random_state=42, shuffle=True)

    all_data_shuffled = []
    all_preds = []
    all_trues = []

    for train_index, test_index in skf.split(all_data, labels):
        x_train = [doc for idx, doc in enumerate(all_data) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(all_data) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]
        # target vector
        le = LabelEncoder()
        y_train_encoded = le.fit_transform(y_train)

        # get textual contexts
        train_textual_context = get_text_tokens(x_train, tokenized=False)
        test_textual_context = get_text_tokens(x_test, tokenized=False)

        # no tokenization
        # tfidf = TfidfVectorizer(tokenizer=dummy_fun, preprocessor=dummy_fun)

        # n-grams
        tfidf = TfidfVectorizer(ngram_range=(1, 2))

        tf_idf_weights = tfidf.fit_transform(train_textual_context)

        # clf = LogisticRegression(max_iter=15000)
        clf = SGDClassifier(max_iter=15000)
        clf.fit(tf_idf_weights, y_train_encoded)
        test_tf_idf_weights = tfidf.transform(test_textual_context)
        predictions = clf.predict(test_tf_idf_weights)
        y_pred = [le.classes_[pred] for pred in predictions]

        """
        print("fold: ", fold_n)
        print(classification_report(y_test, y_pred, zero_division=0.00))
        cm = confusion_matrix(y_test, y_pred, labels=['opposes', 'other', 'supports'])
        print_cm(cm, labels=['opposes', 'other', 'supports'])
        print("\n")
        fold_n += 1
        """

        all_data_shuffled.extend(x_train)
        all_trues.extend(y_test)
        all_preds.extend(y_pred)

    print("\n\nFINAL REPORT")
    print(classification_report(all_trues, all_preds, zero_division=0.00))
    cm = confusion_matrix(all_trues, all_preds, labels=['opposes', 'other', 'supports'])
    print_cm(cm, labels=['opposes', 'other', 'supports'])
    print()

    """
    for x_data, y_pred, y_true in zip(all_data_shuffled,all_trues, all_preds):
        if y_pred == y_true:
            continue
        print('true:', y_true, '\t', 'pred:', y_pred)
        print(x_data)
        print("\n\n---------")
    """


if __name__ == "__main__":
    main()
