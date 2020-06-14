import csv
import numpy as np
import joblib

from collections import Counter

from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder

from keras import Input, Model
from keras.utils import to_categorical
from keras_preprocessing.sequence import pad_sequences
from keras_preprocessing.text import Tokenizer
from keras.losses import categorical_crossentropy
from keras.layers import Dense, Embedding, Bidirectional, LSTM


def collect_training_data():
    data = []
    with open(
            "data/trained_data_political_relationships - annotated_publico.tsv", newline=""
    ) as csvfile:
        titles = csv.reader(csvfile, delimiter="\t", quotechar="|")
        next(titles)
        for row in titles:
            if row[1]:
                data.append({'sentence': row[0], 'label': row[1], 'ent1': row[5], 'ent2': row[6]})

    with open("data/trained_data_political_relationships - antónio_costa.tsv",  newline="") as csvfile:
        titles = csv.reader(csvfile, delimiter="\t", quotechar="|")
        next(titles)
        for row in titles:
            if row[0]:
                data.append({"sentence": row[1], "label": row[2],'ent1': row[6], 'ent2': row[7]})

    return data


def train_tfidf_logit_clf(data):
    docs = [d["sentence"] for d in data]
    labels = [d["label"] for d in data]

    vectorizer = TfidfVectorizer()
    x_data = vectorizer.fit_transform(docs)

    le = preprocessing.LabelEncoder()
    y_data = le.fit_transform(labels)
    clf = LogisticRegressionCV(cv=2, verbose=0).fit(x_data, y_data)
    return clf, vectorizer, le


def load_fasttext_embeddings(file, vocabulary=None):
    embeddings_index = {}
    with open(file) as f_in:
        for line in f_in:
            values = line.split()
            word = values[0]
            if word not in vocabulary:
                continue
            coefs = np.asarray(values[1:], dtype='float32')
            embeddings_index[word] = coefs
    print('Loaded %s word vectors.' % len(embeddings_index))
    return embeddings_index


def create_embeddings_matrix(embeddings_index, word2index, embedding_dim=100):
    embeddings_matrix = np.random.rand(len(word2index) + 1, embedding_dim)
    for word, idx in word2index.items():
        if idx == 0:
            embeddings_matrix[idx] = np.zeros(embedding_dim)
        embedding_vector = embeddings_index.get(word)
        if embedding_vector is not None:
            embeddings_matrix[idx] = embedding_vector

    print('Matrix shape: {}'.format(embeddings_matrix.shape))
    return embeddings_matrix


def get_embeddings_layer(embeddings_matrix, max_len, name='embedding_layer', trainable=False):
    embedding_layer = Embedding(
        input_dim=embeddings_matrix.shape[0],
        output_dim=embeddings_matrix.shape[1],
        input_length=max_len,
        weights=[embeddings_matrix],
        trainable=trainable,
        name=name)
    return embedding_layer


def print_cm(cm, labels, hide_zeroes=False, hide_diagonal=False, hide_threshold=None):
    # taken from here: https://gist.github.com/zachguo/10296432
    """pretty print for confusion matrixes"""
    columnwidth = max([len(x) for x in labels] + [5])  # 5 is value length
    empty_cell = " " * columnwidth

    # Begin CHANGES
    fst_empty_cell = (columnwidth - 3) // 2 * " " + "t/p" + (columnwidth - 3) // 2 * " "

    if len(fst_empty_cell) < len(empty_cell):
        fst_empty_cell = " " * (len(empty_cell) - len(fst_empty_cell)) + fst_empty_cell
    # Print header
    print("    " + fst_empty_cell, end=" ")
    # End CHANGES

    for label in labels:
        print("%{0}s".format(columnwidth) % label, end=" ")

    print()
    # Print rows
    for i, label1 in enumerate(labels):
        print("    %{0}s".format(columnwidth) % label1, end=" ")
        for j in range(len(labels)):
            cell = "%{0}.1f".format(columnwidth) % cm[i, j]
            if hide_zeroes:
                cell = cell if float(cm[i, j]) != 0 else empty_cell
            if hide_diagonal:
                cell = cell if i != j else empty_cell
            if hide_threshold:
                cell = cell if cm[i, j] > hide_threshold else empty_cell
            print(cell, end=" ")
        print()


def train_lstm(x_train, y_train, x_test, y_test):

    # vectorize: convert list of tokens/words to indexes
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(x_train)

    x_train_vec = tokenizer.texts_to_sequences(x_train)

    word2index = tokenizer.word_index
    print("Found %s unique tokens." % len(word2index))

    # add padding token
    word2index['PAD'] = 0
    vocabulary = set(word2index.keys())

    # get the max sentence length, needed for padding
    max_input_length = max([len(x) for x in x_train_vec])
    print("Max. sequence length: ", max_input_length)

    # pad all the sequences of indexes to the 'max_input_length'
    x_train_vec_padded = pad_sequences(
        x_train_vec, maxlen=max_input_length, padding="post", truncating="post"
    )

    # Encode the labels, each must be a vector with dim = num. of possible labels
    le = LabelEncoder()
    y_train_encoded = le.fit_transform(y_train)
    y_train_vec = to_categorical(y_train_encoded, num_classes=None)
    print("Shape of train data tensor:", x_train_vec_padded.shape)
    print("Shape of train label tensor:", y_train_vec.shape)
    num_classes = y_train_vec.shape[1]

    # train
    print("\n")
    embeddings_index = load_fasttext_embeddings('skip_s100.txt', vocabulary=vocabulary)
    word_no_vectors = vocabulary.difference(set(embeddings_index.keys()))
    embeddings_matrix = create_embeddings_matrix(embeddings_index, word2index)
    print("vocabulary: ", len(vocabulary))
    print("words without a vector: ", len(word_no_vectors))
    print()

    index2word = {v: k for k, v in word2index.items()}
    for idx_vector, sentence in zip(x_train_vec_padded, x_train):
        for idx in idx_vector:
            if idx == 0 or index2word[idx] in word_no_vectors:
                continue
            np.testing.assert_array_equal(embeddings_index[index2word[idx]], embeddings_matrix[idx])

    # create the embedding layer
    print("\n")
    embedding_layer = get_embeddings_layer(embeddings_matrix, max_input_length, trainable=True)

    # connect the input with the embedding layer
    i = Input(shape=(max_input_length,), dtype='int32', name='main_input')
    x = embedding_layer(i)

    lstm_out = Bidirectional(LSTM(256, dropout=0.3, recurrent_dropout=0.3))(x)
    o = Dense(num_classes, activation='softmax', name='output')(lstm_out)

    model = Model(inputs=i, outputs=o)
    model.compile(loss={'output': categorical_crossentropy},
                  optimizer='adam', metrics=['accuracy'])

    model.fit(x_train_vec_padded, y_train_vec, epochs=25)

    # apply to test data
    x_test_vec = tokenizer.texts_to_sequences(x_test)
    x_test_vec_padded = pad_sequences(
        x_test_vec, maxlen=max_input_length, padding="post", truncating="post"
    )

    predicted_probs = model.predict(x_test_vec_padded)
    labels_idx = np.argmax(predicted_probs, axis=1)
    pred_labels = le.inverse_transform(labels_idx)

    """
    for sent, label in zip(x_test, pred_labels):
        print(sent, "\t", label)
    """

    print(classification_report(y_test, pred_labels))

    cm = confusion_matrix(y_test, pred_labels, labels=le.classes_)
    print_cm(cm, labels=le.classes_)


def main():
    data = collect_training_data()
    print("\nSamples per class:")
    for k, v in Counter(d["label"] for d in data).items():
        print(k, '\t', v)
    print("\nTotal nr. messages:\t", len(data))
    print("\n")

    docs = [(d["sentence"], d['ent1'], d['ent2']) for d in data]
    labels = [d["label"] for d in data]

    # replace entity name by 'PER'
    docs = [d[0].replace(d[1], 'PER').replace(d[2], 'PER') for d in docs]

    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    for train_index, test_index in skf.split(docs, labels):
        x_train = [doc for idx, doc in enumerate(docs) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(docs) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]

    train_lstm(x_train, y_train, x_test, y_test)
    exit(-1)

    clf, vectorizer, le = train_tfidf_logit_clf(data)
    predicted_probs = clf.predict_proba(vectorizer.transform(docs))

    print(predicted_probs)
    print(type(predicted_probs))
    print(predicted_probs.shape)

    labels_idx = np.argmax(predicted_probs, axis=1)
    pred_labels = le.inverse_transform(labels_idx)

    for sent, label in zip(docs, pred_labels):
        print(sent, "\t", label)

    print(classification_report(labels, pred_labels))

    joblib.dump(clf, "relationship_clf.joblib")
    joblib.dump(vectorizer, "vectorizer.joblib")
    joblib.dump(le, "label_encoder.joblib")


if __name__ == "__main__":
    main()
