import re
import json
from sklearn.preprocessing import scale

import numpy as np
import joblib
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC

from politiquices.nlp.classifiers.direction.relationship_direction_clf import DirectionClassifier
from politiquices.nlp.classifiers.relationship.sentiment import WordSentiment
from politiquices.nlp.classifiers.utils.ml_utils import print_cm
from politiquices.nlp.utils.utils import (
    read_ground_truth,
    find_sub_list
)

nlp = spacy.load(
    "pt_core_news_lg",
    disable=["tagger", "ner", "attribute_ruler"],
)

word_sentiment = WordSentiment()

direction_clf = DirectionClassifier()

# for error analysis
supports_classified_as_opposes = []
supports_classified_as_other = []
opposes_classified_as_supports = []
opposes_classified_as_other = []
other_classified_as_supports = []
other_classified_as_opposes = []
supports_correct = []
opposes_correct = []
other_correct = []


def error_analysis(y_pred, y_test, all_data_test):

    for pred, true, sample in zip(y_pred, y_test, all_data_test):

        # supports misclassified
        if true == 'supports' and pred == 'opposes':
            supports_classified_as_opposes.append(sample)
        if true == 'supports' and pred == 'other':
            supports_classified_as_other.append(sample)

        # opposes misclassified
        if true == 'opposes' and pred == 'supports':
            opposes_classified_as_supports.append(sample)
        if true == 'opposes' and pred == 'other':
            opposes_classified_as_other.append(sample)

        # other misclassified
        if true == 'other' and pred == 'supports':
            other_classified_as_supports.append(sample)
        if true == 'other' and pred == 'opposes':
            other_classified_as_opposes.append(sample)

        # correct
        if true == 'supports' and pred == 'supports':
            supports_correct.append(sample)
        if true == 'opposes' and pred == 'opposes':
            opposes_correct.append(sample)
        if true == 'other' and pred == 'other':
            other_correct.append(sample)


def remap_y_target(y_labels):
    return [re.sub(r"_?ent[1-2]_?", "", y_sample) if y_sample != 'other' else 'other'
            for y_sample in y_labels]


def class_feature_importance(X, Y, feature_importances):
    # Take from: https://stackoverflow.com/questions/35249760
    N, M = X.shape
    X = scale(X)

    out = {}
    for c in set(Y):
        out[c] = dict(
            zip(range(N), np.mean(X[Y == c, :], axis=0) * feature_importances)
        )

    return out


def features_importance():

    X = np.array([[2, 2, 2, 0, 3, -1],
                  [2, 1, 2, -1, 2, 1],
                  [0, -3, 0, 1, -2, 0],
                  [-1, -1, 1, 1, -1, -1],
                  [-1, 0, 0, 2, -3, 1],
                  [2, 2, 2, 0, 3, 0]], dtype=float)

    Y = np.array([0, 0, 1, 1, 1, 0])
    feature_importances = np.array([0.1, 0.2, 0.3, 0.2, 0.1, 0.1])
    # feature_importances = model._feature_importances

    result = class_feature_importance(X, Y, feature_importances)


def get_contexts(title_pos_tags, ent1, ent2):
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
            before = title_pos_tags[0:ent1_start]
            return before, between, after


def get_text_tokens(x_data, tokenized=True, filter_pos=False):
    # ToDo: gather more of these contexts
    #
    #       'considera aprovação da moção de'
    #       'acredita que detenção de'
    #       'diz que visitas de'

    # ToDo: who is the subject/agent of the sentence ?
    #
    # 'PT critica falso vídeo de Lula a apoiar Marina'
    #   -> nsubj: PT, obj: Marina
    # 'Mulher e filha de Mário Soares apoiam campanha de Fernando Nobre'
    #   -> nsubj: Mulher (e filha)
    # 'PS acusa Pacheco Pereira de caluniar José Sócrates com declarações sobre TVI'
    #   -> nsubj: PS
    # 'CDS acusa Costa de afirmar "linhagem de José Sócrates"'
    #   -> nsubj: CDS
    # 'PSD desafia Seguro a esclarecer se concorda com Pedro Nuno Santos'
    #   -> nsubj: PSD
    # 'Eleitores consideram Sócrates melhor líder que Passos Coelho'
    #   -> nsubj: Eleitores
    # 'BE: José Gusmão ironiza sobre apoio de Coentrão a Sócrates'

    # ToDo: who is the object of the sentence ?
    #
    # Assunção Esteves demite assessor que dava apoio a candidatura autárquica de Almeida Henriques

    # ToDo: how does the syntatic parse tree for sentences like these look like?
    #
    # Passos defende estabilidade, Cavaco afirma isenção da sua candidatura
    #   2 pairs: nsubj, obj; nsubj, obj
    # 'Costa já promete ministérios. E tem o apoio do genro de Cavaco'
    # Jorge Coelho sai do secretariado nacional do PS e Ana Gomes chega à direcção do partido
    # Sócrates confiante em vitória “expressiva”, António Costa apela à mobilização

    if filter_pos:
        filter_only_pos = ['ADV', 'NOUN', 'VERB', 'ADJ']

    stop_words = ['a', 'o', 'as', 'os']
    to_clean = ['"']

    cntxt_a_aft = ['diz a', 'responde a', 'sugere a', 'diz que atitude de']
    cntxt_b_aft = ['diz que', 'afirma que', 'espera que', 'defende que', 'considera que']
    cntxt_c_aft = ['considera']
    cntxt_d_aft = [':', '.', ',', '. "']
    context_aft = cntxt_a_aft + cntxt_b_aft + cntxt_c_aft + cntxt_d_aft

    cntxt_a_bef = [', sugere']

    textual_context = []
    for x in x_data:
        title = x['title']
        ent1 = x['ent1']
        ent2 = x['ent2']
        doc = nlp(title)
        pos_tags = [t for t in doc]
        before, between, after = get_contexts(pos_tags, ent1, ent2)
        context_text = ' '.join([t.text for t in between])
        if tokenized:

            # 'sentiment' is on AFT context
            if context_text in context_aft:
                context_text = [t.lemma_ for t in after if t.text not in stop_words]

            # 'sentiment' is on BEF context
            # elif context_text in cntxt_a_bef:
            #   context_text = [t.lemma_ for t in before]

            # 'sentiment' is on BET context
            else:
                context_text = [t.lemma_ for t in between if t.text not in stop_words]

        textual_context.append(context_text)

    return textual_context


def train_all_data(all_data, labels):
    # y: labels
    le = LabelEncoder()
    y_train_encoded = le.fit_transform(labels)

    # x: custom  tokenization
    tfidf = TfidfVectorizer(tokenizer=dummy_fun, preprocessor=dummy_fun)
    train_textual_context = get_text_tokens(all_data, tokenized=True)
    tf_idf_weights = tfidf.fit_transform(train_textual_context)
    clf = LinearSVC(class_weight='balanced', verbose=1)
    clf.fit(tf_idf_weights, y_train_encoded)
    joblib.dump(clf, filename='linear_svm.joblib')


def dummy_fun(doc):
    return doc


def main():
    all_data = read_ground_truth("../politiquices_data_v1.0.csv")
    labels = remap_y_target([s['label'] for s in all_data])
    skf = StratifiedKFold(n_splits=4, random_state=42, shuffle=True)

    all_data_shuffled = []
    all_predictions = []
    all_trues = []
    fold_n = 0

    for train_index, test_index in skf.split(all_data, labels):
        print(f"fold: {fold_n}")
        x_train = [doc for idx, doc in enumerate(all_data) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(all_data) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]
        all_data_test = [label for idx, label in enumerate(all_data) if idx in test_index]

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
            preprocessor=dummy_fun,
            ngram_range=(1, 2)
        )

        # n-grams
        # tfidf = TfidfVectorizer(ngram_range=(1, 2))
        tf_idf_weights = tfidf.fit_transform(train_textual_context)

        # clf = LogisticRegression(multi_class='multinomial', class_weight='balanced')
        # clf = SGDClassifier(max_iter=15000, class_weight='balanced')
        clf = LinearSVC(class_weight='balanced', max_iter=2000)

        clf.fit(tf_idf_weights, y_train_encoded)
        test_tf_idf_weights = tfidf.transform(test_textual_context)
        predictions = clf.predict(test_tf_idf_weights)
        y_pred = [le.classes_[pred] for pred in predictions]

        all_data_shuffled.extend(x_train)
        all_trues.extend(y_test)
        all_predictions.extend(y_pred)
        error_analysis(y_pred, y_test, all_data_test)
        fold_n += 1

    # other classified as supports
    for sample in other_classified_as_supports:
        print(sample['title'])
        print("ent1: ", sample['ent1'])
        print("ent2: ", sample['ent2'])
        print("true: other")
        print("pred: supports")
        doc = nlp(sample['title'])
        pos_tags = [t for t in doc]
        before, between, after = get_contexts(pos_tags, sample['ent1'], sample['ent2'])
        print("BEF: ", before)
        print("BET: ", between)
        print("AFT: ", after)
        print("features used: ", get_text_tokens([sample]))
        print()
        for token in doc:
            if token.dep_ == 'nsubj':
                print(token.text, list(token.children))
                if not (token.text in sample['ent1'] or token.text in sample['ent2']):
                    print("entities not related")
        """
        for token in doc:
            print(f"{token.text:<10} \t {token.dep_:>10} \t {list(token.children)}")
        """
        # print("features tags: ", [(t.text, t.lemma_, t.pos_) for t in pos_tags])
        print("\n\n\n--------------")

    # supports classified as opposes
    """
    for sample in supports_classified_as_opposes:
        print(sample['title'])
        print("true: supports")
        print("pred: opposes")
        doc = nlp(sample['title'])
        pos_tags = [t for t in doc]
        before, between, after = get_contexts(pos_tags, sample['ent1'], sample['ent2'])
        print("BEF: ", before)
        print("BET: ", between)
        print("AFT: ", after)
        print("features used: ", get_text_tokens([sample]))
        # print("features tags: ", [(t.text, t.lemma_, t.pos_) for t in pos_tags])
        print("\n\n--------------")
    """

    # opposes classified as supports
    """
    for sample in opposes_classified_as_supports:
        print(sample['title'])
        print(sample['label'])
        print("true: opposes")
        print("pred: supports")
        doc = nlp(sample['title'])
        pos_tags = [t for t in doc]
        before, between, after = get_contexts(pos_tags, sample['ent1'], sample['ent2'])
        print("BEF: ", before)
        print("BET: ", between)
        print("AFT: ", after)
        print("features used: ", get_text_tokens([sample]))
        # print("features tags: ", [(t.text, t.lemma_, t.pos_) for t in pos_tags])
        print("\n\n--------------")
    """

    # apply direction classifier to those that were correct
    """
    for sample in supports_correct + opposes_correct:
        title = sample['title']
        ent1 = sample['ent1']
        ent2 = sample['ent2']
        pred_direction, pattern, context, tags = direction_clf.detect_direction(title, ent1, ent2)
        print(title)
        print(sample['label'])
        print(pred_direction)
        print("\n\n--------------")
    """

    print("\n\nFINAL REPORT")
    print(classification_report(all_trues, all_predictions, zero_division=0.00))
    cm = confusion_matrix(all_trues, all_predictions, labels=['opposes', 'other', 'supports'])
    print_cm(cm, labels=['opposes', 'other', 'supports'])
    print()


if __name__ == "__main__":
    main()
