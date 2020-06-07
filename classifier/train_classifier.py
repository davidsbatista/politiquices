import csv
import numpy as np
import joblib

from collections import Counter

from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import classification_report
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
            "data/trained_data_political_relationships - extracted_info.tsv", newline=""
    ) as csvfile:
        titles = csv.reader(csvfile, delimiter="\t", quotechar="|")
        next(titles)
        for row in titles:
            if row[1]:
                data.append({"sentence": row[0], "label": row[1]})

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


def train_lstm(data):
    docs = [d["sentence"] for d in data]
    labels = [d["label"] for d in data]

    # vectorize: convert list of tokens/words to indexes
    x_all = [sent for sent in docs]
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(x_all)
    sequences_train = tokenizer.texts_to_sequences(x_all)
    word2index = tokenizer.word_index
    print("Found %s unique tokens." % len(word2index))

    # add padding token
    word2index['PAD'] = 0

    vocabulary = set(word2index.keys())

    # padding
    # get the max sentence length, needed for padding
    max_input_length = max([len(x) for x in x_all])
    print("Max. sequence length: ", max_input_length)

    # pad all the sequences of indexes to the 'max_input_length'
    x_all_padded = pad_sequences(
        sequences_train, maxlen=max_input_length, padding="post", truncating="post"
    )

    # Encode the labels, each must be a vector with dim = num. of possible labels
    le = LabelEncoder()
    labels_encoded_train = le.fit_transform(labels)
    categorical_labels_train = to_categorical(labels_encoded_train, num_classes=None)
    print("Shape of train data tensor:", x_all_padded.shape)
    print("Shape of train label tensor:", categorical_labels_train.shape)

    num_classes = categorical_labels_train.shape[1]

    # train
    embeddings_index = load_fasttext_embeddings('skip_s100.txt', vocabulary=vocabulary)

    print(len(vocabulary))
    print("words without a vector:")
    word_no_vectors = vocabulary.difference(set(embeddings_index.keys()))
    embeddings_matrix = create_embeddings_matrix(embeddings_index, word2index)

    index2word = {v: k for k, v in word2index.items()}
    for idx_vector, sentence in zip(x_all_padded, docs):
        for idx in idx_vector:
            if idx == 0 or index2word[idx] in word_no_vectors:
                continue
            np.testing.assert_array_equal(embeddings_index[index2word[idx]], embeddings_matrix[idx])

    # create the embedding layer
    embedding_layer = get_embeddings_layer(embeddings_matrix, max_input_length, trainable=True)

    # connect the input with the embedding layer
    i = Input(shape=(max_input_length,), dtype='int32', name='main_input')
    x = embedding_layer(i)

    lstm_out = Bidirectional(LSTM(64, dropout=0.2, recurrent_dropout=0.2))(x)
    o = Dense(num_classes, activation='softmax', name='output')(lstm_out)

    model = Model(inputs=i, outputs=o)
    model.compile(loss={'output': categorical_crossentropy},
                  optimizer='adam', metrics=['accuracy'])

    model.fit(x_all_padded, categorical_labels_train, epochs=10)

    predicted_probs = model.predict(x_all_padded)

    print(predicted_probs)
    print(type(predicted_probs))
    print(predicted_probs.shape)

    labels_idx = np.argmax(predicted_probs, axis=1)
    pred_labels = le.inverse_transform(labels_idx)

    for sent, label in zip(docs, pred_labels):
        print(sent, "\t", label)

    print(classification_report(labels, pred_labels))


def main():
    data = collect_training_data()
    for k, v in Counter(d["label"] for d in data).items():
        print(k, v)
    print(len(data))

    train_lstm(data)
    exit(-1)

    clf, vectorizer, le = train_tfidf_logit_clf(data)
    docs = [d["sentence"] for d in data]
    labels = [d["label"] for d in data]

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
