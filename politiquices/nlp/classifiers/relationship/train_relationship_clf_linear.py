import re

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC

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

word_sentiment = WordSentiment()

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
            between = title_pos_tags[ent1_end + 1: ent2_start]
            after = title_pos_tags[ent2_end+1:]
            return between, after


def get_pos_tags(sentence):
    doc = nlp(sentence)
    return [t for t in doc]


def remap_y_target(y_labels):
    return ['other' if y_sample in other_labels else re.sub(r"_?ent[1-2]_?", "", y_sample)
            for y_sample in y_labels]


def get_text_tokens(x_data, tokenized=True):
    # select only, NOUN, VERB, ADJ
    filter_only_pos = ['ADV', 'NOUN', 'VERB', 'ADJ']

    textual_context = []
    for x in x_data:
        title = x['title']
        ent1 = x['ent1']
        ent2 = x['ent2']
        pos_tags = get_pos_tags(title)
        between, after = get_context(pos_tags, ent1, ent2)
        context_text = ' '.join([t.text for t in between])

        if tokenized:
            if context_text == 'diz que':
                # context_text = [t.lemma_ for t in after if t.pos_ in filter_only_pos]
                context_text = [t.lemma_ for t in after]
            else:
                # context_text = [t.lemma_ for t in between if t.pos_ in filter_only_pos]
                context_text = [t.lemma_ for t in between]
        else:
            context_text = ' '.join([t.text for t in between])

        textual_context.append(context_text)

    return textual_context


def dummy_fun(doc):
    return doc


def get_features(textual_context):
    pass


def main():
    training_data = read_ground_truth("../../../politiquices_training_data.tsv")
    training_data_webapp = read_ground_truth("../../api_annotations/annotations_from_webapp.tsv")
    all_data = training_data + training_data_webapp
    labels = remap_y_target([s['label'] for s in all_data])
    skf = StratifiedKFold(n_splits=10, random_state=42, shuffle=True)

    all_data_shuffled = []
    all_preds = []
    all_trues = []
    fold_n = 0

    supports_missclassifed_as_opposes = []
    opposes_missclassifed_as_supports = []
    supports_missclassifed_as_other = []

    for train_index, test_index in skf.split(all_data, labels):
        print(f"fold: {fold_n}")
        x_train = [doc for idx, doc in enumerate(all_data) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(all_data) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]

        # target vector
        le = LabelEncoder()
        y_train_encoded = le.fit_transform(y_train)

        # get textual contexts
        train_textual_context = get_text_tokens(x_train, tokenized=True)
        test_textual_context = get_text_tokens(x_test, tokenized=True)

        # get other features
        # train_other_features = get_features(train_textual_context)
        # test_other_features = get_features(test_textual_context)

        # no tokenization
        tfidf = TfidfVectorizer(
            tokenizer=dummy_fun,
            preprocessor=dummy_fun
        )

        # n-grams
        # tfidf = TfidfVectorizer(ngram_range=(1, 2))
        tf_idf_weights = tfidf.fit_transform(train_textual_context)

        """
        clf = LogisticRegression(
            max_iter=15000,
            multi_class='multinomial',
            n_jobs=5,
        )
        """
        # clf = SGDClassifier(max_iter=15000)
        clf = LinearSVC(class_weight='balanced')

        clf.fit(tf_idf_weights, y_train_encoded)
        test_tf_idf_weights = tfidf.transform(test_textual_context)
        predictions = clf.predict(test_tf_idf_weights)
        y_pred = [le.classes_[pred] for pred in predictions]

        all_data_shuffled.extend(x_train)
        all_trues.extend(y_test)
        all_preds.extend(y_pred)

        for pred, true, sample in zip(y_pred, y_test, x_test):
            if pred == 'opposes' and true == 'supports':
                supports_missclassifed_as_opposes.append(sample)
            if pred == 'supports' and true == 'opposes':
                opposes_missclassifed_as_supports.append(sample)
            if pred == 'other' and true == 'supports':
                supports_missclassifed_as_other.append(sample)

        fold_n += 1

    print("\n\nFINAL REPORT")
    print(classification_report(all_trues, all_preds, zero_division=0.00))
    cm = confusion_matrix(all_trues, all_preds, labels=['opposes', 'other', 'supports'])
    print_cm(cm, labels=['opposes', 'other', 'supports'])
    print()

    """
    for sample in supports_missclassifed_as_other:
        print(sample)
        pos_tags = get_pos_tags(sample['title'])
        between, after = get_context(pos_tags, sample['ent1'], sample['ent2'])
        print(between)
        print(after)
        print("\n\n--------------")

    print("supports_missclassifed_as_other")
    print(len(supports_missclassifed_as_other))
    """


if __name__ == "__main__":
    main()
