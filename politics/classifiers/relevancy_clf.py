import csv
from datetime import datetime
import joblib
import regex
import numpy as np

from keras import Input, Model
from keras.backend import categorical_crossentropy
from keras.layers import Bidirectional, Dense, LSTM
from keras.utils import to_categorical
from keras_preprocessing.sequence import pad_sequences
from sklearn.metrics import classification_report, confusion_matrix

from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder

from politics.classifiers.embeddings_utils import (
    create_embeddings_matrix,
    get_embeddings,
    get_embeddings_layer,
    vectorize_titles,
)
from politics.utils import clean_title, print_cm
from politics.utils.ml_utils import plot_precision_recall_curve, plot_precision_recall_vs_threshold


def read_raw_data(filename):
    data = []
    with open(filename, newline="") as csvfile:
        arquivo = csv.reader(csvfile, delimiter="\t", quotechar="|")
        for row in arquivo:
            data.append(
                {
                    "title": row[0],
                    "label": row[1],
                    "ent_1": row[2],
                    "ent_2": row[3],
                    "date": row[4],
                    "url": row[5],
                }
            )
    return data


class RelevancyClassifier:
    def __init__(self, epochs=20, directional=False):
        self.epochs = epochs
        self.directional = directional
        self.max_input_length = None
        self.model = None
        self.word2index = None
        self.label_encoder = None
        self.num_classes = None
        self.history = None  # ToDo: make function to plot loss graphs on train and test

    def get_model(self, embedding_layer):
        i = Input(shape=(self.max_input_length,), dtype="int32", name="main_input")
        x = embedding_layer(i)
        lstm_out = Bidirectional(LSTM(128, dropout=0.3, recurrent_dropout=0.3))(x)
        o = Dense(self.num_classes, activation="softmax", name="output")(lstm_out)
        model = Model(inputs=i, outputs=o)
        model.compile(
            loss={"output": categorical_crossentropy}, optimizer="adam", metrics=["accuracy"]
        )

        return model

    def train(self, x_train, y_train, word2index, word2embedding):

        x_train_vec = vectorize_titles(word2index, x_train)

        # get the max sentence length, needed for padding
        self.max_input_length = max([len(x) for x in x_train_vec])
        print("Max. sequence length: ", self.max_input_length)

        # pad all the sequences of indexes to the 'max_input_length'
        x_train_vec_padded = pad_sequences(
            x_train_vec, maxlen=self.max_input_length, padding="post", truncating="post"
        )

        # Encode the labels, each must be a vector with dim = num. of possible labels
        # also train relationships directions or not?
        if self.directional is False:
            y_train = [regex.sub(r"_?ent[1-2]_?", "", y_sample) for y_sample in y_train]

        le = LabelEncoder()
        y_train_encoded = le.fit_transform(y_train)
        y_train_vec = to_categorical(y_train_encoded, num_classes=None)
        print("Shape of train data tensor:", x_train_vec_padded.shape)
        print("Shape of train label tensor:", y_train_vec.shape)
        self.num_classes = y_train_vec.shape[1]

        # create the embedding layer
        embeddings_matrix = create_embeddings_matrix(word2embedding, word2index)
        embedding_layer = get_embeddings_layer(
            embeddings_matrix, self.max_input_length, trainable=True
        )
        print("embeddings_matrix: ", embeddings_matrix.shape)

        model = self.get_model(embedding_layer)

        # ToDo: plot loss graphs on train and test
        self.history = model.fit(x_train_vec_padded, y_train_vec, epochs=self.epochs)
        self.model = model
        self.word2index = word2index
        self.label_encoder = le

    def tag(self, x_test):
        x_test_vec = vectorize_titles(self.word2index, x_test)
        x_test_vec_padded = pad_sequences(
            x_test_vec, maxlen=self.max_input_length, padding="post", truncating="post"
        )
        return self.model.predict(x_test_vec_padded)

    def evaluate(self, x_test, y_test):

        # ToDo: save this as in a report format
        if not self.model:
            pass

        # Encode the labels, each must be a vector with dim = num. of possible labels
        if self.directional is False:
            y_test = [regex.sub(r"_?ent[1-2]_?", "", y_sample) for y_sample in y_test]

        x_predicted_probs = self.tag(x_test)

        labels_idx = np.argmax(x_predicted_probs, axis=1)
        pred_labels = self.label_encoder.inverse_transform(labels_idx)
        print("\n" + classification_report(y_test, pred_labels))
        report = classification_report(y_test, pred_labels, output_dict=True)
        cm = confusion_matrix(y_test, pred_labels, labels=self.label_encoder.classes_)
        print_cm(cm, labels=self.label_encoder.classes_)
        print()

        precision_vals, recall_vals, thresholds = plot_precision_recall_curve(
            x_predicted_probs, y_test, "relevant", "precision_recall_curve"
        )

        plot_precision_recall_vs_threshold(
            precision_vals, recall_vals, thresholds, "precision_recall_vd_threshold"
        )

        for sent, true_label, pred_label, prob in zip(
            x_test, y_test, pred_labels, x_predicted_probs
        ):
            if true_label != pred_label:
                print(sent, "\t\t", true_label, "\t\t", pred_label, prob)
        print()

        return report

    def save(self):
        date_time = datetime.now().strftime("%Y-%m-%d_%H:%m:%S")
        joblib.dump(self, f"trained_models/relevancy_clf_{date_time}.pkl")


def main():
    data = read_raw_data("../../data/annotated/arquivo.tsv")

    for entry in data:
        entry['title'] = clean_title(entry['title']).strip()

    # sentences without any label are considered non-relevant
    all_pos_titles = set([clean_title(x["title"]) for x in data if x["label"]])
    all_neg_titles = set([clean_title(x["title"]) for x in data if x["label"] == ""])

    data = [(x, "relevant") for x in all_pos_titles]
    data.extend([(x, "non-relevant") for x in all_neg_titles])
    docs = [x[0] for x in data]
    labels = [x[1] for x in data]

    word2embedding, word2index = get_embeddings()

    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    for train_index, test_index in skf.split(docs, labels):
        x_train = [doc for idx, doc in enumerate(docs) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(docs) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]

        model = RelevancyClassifier(directional=False, epochs=20)
        model.train(x_train, y_train, word2index, word2embedding)
        report = model.evaluate(x_test, y_test)
        print(report)

    model = RelevancyClassifier(directional=True, epochs=2)
    model.train(docs, labels, word2index, word2embedding)
    model.save()


if __name__ == "__main__":
    main()