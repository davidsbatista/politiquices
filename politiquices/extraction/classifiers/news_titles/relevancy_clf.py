import numpy as np

np.random.seed(1337)  # for reproducibility
import random as python_random

python_random.seed(123)  # for reproducibility
import tensorflow as tf

tf.random.set_seed(1234)    # for reproducibility

import pickle
from collections import Counter
from datetime import datetime

import joblib

from keras import Input, Model
from keras.callbacks import ModelCheckpoint
from keras.engine import Layer
from keras.engine.saving import save_model
from keras.layers import Bidirectional, Dense, LSTM
from keras.losses import categorical_crossentropy
from keras.utils import to_categorical
from keras_preprocessing.sequence import pad_sequences
from keras.backend import categorical_crossentropy

from tensorflow.keras import backend as K

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

from politiquices.extraction.classifiers.news_titles.plot_graphs import plot_loss_acc, plot_metrics
from politiquices.extraction.utils import print_cm
from politiquices.extraction.utils.utils import clean_title_re
from politiquices.extraction.classifiers.news_titles.embeddings_utils import (
    create_embeddings_matrix,
    get_embeddings_layer,
    vectorize_titles,
)
from politiquices.extraction.utils.utils import clean_title_quotes


def pre_process_train_data(data):
    """

    :param data:
    :return:
    """
    other = [
        "other",
        "ent1_replaces_ent2",
        "ent2_replaces_ent1",
        "meet_together",
        "ent1_asks_support_ent2",
        "ent2_asks_support_ent1",
        "mutual_disagreement",
        "mutual_agreement",
        "ent1_asks_action_ent2",
        "more_entities",
    ]

    titles = []
    labels = []

    for d in data:
        titles.append(clean_title_quotes((clean_title_re(d["title"]))))
        if d["label"] in other:
            labels.append("other")
        else:
            labels.append("relevant")

    print("\nSamples per class:")
    for k, v in Counter(labels).items():
        print(k, "\t", v)
    print("\nTotal nr. messages:\t", len(data))
    print("\n")

    # replace entity name by 'PER'
    # titles = [d[0].replace(d[1], "PER").replace(d[2], "PER") for d in titles]

    return titles, labels


class Attention(Layer):
    def __init__(self, **kwargs):
        super(Attention, self).__init__(**kwargs)

    def build(self, input_shape):
        self.W = self.add_weight(
            name="att_weight", shape=(input_shape[-1], 1), initializer="normal"
        )
        self.b = self.add_weight(name="att_bias", shape=(input_shape[1], 1), initializer="zeros")
        super(Attention, self).build(input_shape)

    def call(self, x, **kwargs):
        et = K.squeeze(K.tanh(K.dot(x, self.W) + self.b), axis=-1)
        at = K.softmax(et)
        at = K.expand_dims(at, axis=-1)
        output = x * at
        return K.sum(output, axis=1)

    def compute_output_shape(self, input_shape):
        return input_shape[0], input_shape[-1]

    def get_config(self):
        return super(Attention, self).get_config()


class LSTMAtt:
    def __init__(self, epochs=20, directional=False):
        self.epochs = epochs
        self.directional = directional
        self.max_input_length = None
        self.word2index = None
        self.label_encoder = None
        self.num_classes = None
        self.model = None

    def get_model(self, embedding_layer):

        i = Input(shape=(self.max_input_length,), dtype="int32", name="main_input")
        x = embedding_layer(i)
        lstm_out = Bidirectional(
            LSTM(128, dropout=0.3, recurrent_dropout=0.3, return_sequences=True)
        )(x)
        att_out = Attention()(lstm_out)
        o = Dense(self.num_classes, activation="softmax", name="output")(att_out)
        model = Model(inputs=i, outputs=o)
        model.compile(
            loss={"output": categorical_crossentropy}, optimizer="adam", metrics=["accuracy"]
        )

        return model

    def train(self, x_train, y_train, word2index, word2embedding, x_val=None, y_val=None):

        x_train_vec = vectorize_titles(word2index, x_train, save_tokenized=False, save_missed=False)

        # get the max sentence length, needed for padding
        self.max_input_length = max([len(x) for x in x_train_vec])
        print("Max. sequence length: ", self.max_input_length)

        # pad all the sequences of indexes to the 'max_input_length'
        x_train_vec_padded = pad_sequences(
            x_train_vec, maxlen=self.max_input_length, padding="post", truncating="post"
        )

        if x_val and y_val:
            x_val_vec = vectorize_titles(word2index, x_val, save_tokenized=False, save_missed=False)
            x_val_vec_padded = pad_sequences(
                x_val_vec, maxlen=self.max_input_length, padding="post", truncating="post"
            )

        # Encode the labels, each must be a vector with dim = num. of possible labels
        print("y_train: ", len(y_train))

        le = LabelEncoder()
        y_train_encoded = le.fit_transform(y_train)
        y_train_vec = to_categorical(y_train_encoded, num_classes=None)
        print("Shape of train data tensor:", x_train_vec_padded.shape)
        print("Shape of train label tensor:", y_train_vec.shape)
        self.num_classes = y_train_vec.shape[1]
        self.label_encoder = le

        if y_val:
            val_y_vec = to_categorical(le.transform(y_val))

        # compute class weights
        nr_other = y_train.count("other")
        nr_relevant = y_train.count("relevant")
        total = len(y_train)

        # Scaling by total/2 helps keep the loss to a similar magnitude.
        # The sum of the weights of all examples stays the same.
        weight_for_0 = (1 / nr_other) * total
        weight_for_1 = (1 / nr_relevant) * total

        class_weight = {0: weight_for_0, 1: weight_for_1}
        print("Weight for class 0 (other) : {:.2f}".format(weight_for_0))
        print("Weight for class 1 (relevant): {:.2f}".format(weight_for_1))

        # create the embedding layer
        embeddings_matrix = create_embeddings_matrix(word2embedding, word2index)
        embedding_layer = get_embeddings_layer(
            embeddings_matrix, self.max_input_length, trainable=True
        )
        print("embeddings_matrix: ", embeddings_matrix.shape)

        model = self.get_model(embedding_layer)

        callbacks = []
        if x_val and y_val:
            from .callbacks import Metrics

            metrics = Metrics(**{"le": self.label_encoder})
            callbacks = [metrics]
            val_data = (x_val_vec_padded, val_y_vec)
        else:
            val_data = None

        history = model.fit(
            x_train_vec_padded,
            y_train_vec,
            validation_data=val_data,
            epochs=self.epochs,
            class_weight=class_weight,
            callbacks=callbacks,
            batch_size=16,
        )

        # plots go here
        if x_val and y_val:
            pass
            # plot_metrics(metrics.metrics_at_epoch)
            # plot_loss_acc(history)

        self.word2index = word2index
        self.label_encoder = le

        return model

    def tag(self, x_test, log=False):
        x_test_vec = vectorize_titles(
            self.word2index, x_test, log=log, save_tokenized=False, save_missed=False
        )

        x_test_vec_padded = pad_sequences(
            x_test_vec, maxlen=self.max_input_length, padding="post", truncating="post"
        )
        return self.model.predict(x_test_vec_padded)

    def evaluate(self, x_test, y_test):

        if not self.model:
            raise Exception("model not trained or not present")

        x_predicted_probs = self.tag(x_test)

        scores = []
        for preds in x_predicted_probs:
            rel_type_scores = {
                label: float(score) for score, label in zip(preds, self.label_encoder.classes_)
            }
            scores.append(rel_type_scores)

        labels_idx = np.argmax(x_predicted_probs, axis=1)
        pred_labels = self.label_encoder.inverse_transform(labels_idx)
        print("\n" + classification_report(y_test, pred_labels))
        report_str = "\n" + classification_report(y_test, pred_labels)
        cm = confusion_matrix(y_test, pred_labels, labels=self.label_encoder.classes_)
        print_cm(cm, labels=self.label_encoder.classes_)
        print()

        misclassifications = []
        correct_classifications = []
        for title, pred_y, true_y, scores in zip(x_test, pred_labels, y_test, scores):
            if pred_y != true_y:
                misclassifications.append([title, pred_y, true_y, scores])
            if pred_y == true_y:
                correct_classifications.append([title, pred_y, true_y, scores])

        return report_str, misclassifications, correct_classifications

    def save(self, keras_model, fold=None):
        date_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        if fold:
            f_name = f"trained_models/relevancy_clf_fold_{str(fold)}_{date_time}"
        else:
            f_name = f"trained_models/relevancy_clf_{date_time}"

        # save Keras model to a different file
        save_model(keras_model, f_name + ".h5")

        with open(f"{f_name}" + ".pkl", "wb") as f_out:
            pickle.dump(self, f_out)


class RelevancyClassifier:
    def __init__(self, epochs=20, directional=False):
        self.epochs = epochs
        self.directional = directional
        self.max_input_length = None
        self.model = None
        self.word2index = None
        self.label_encoder = None
        self.num_classes = None
        self.history = None

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
        x_train_vec = vectorize_titles(word2index, x_train, save_tokenized=False, save_missed=False)

        # get the max sentence length, needed for padding
        self.max_input_length = max([len(x) for x in x_train_vec])
        print("Max. sequence length: ", self.max_input_length)

        # pad all the sequences of indexes to the 'max_input_length'
        x_train_vec_padded = pad_sequences(
            x_train_vec, maxlen=self.max_input_length, padding="post", truncating="post"
        )

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

        self.history = model.fit(x_train_vec_padded, y_train_vec, epochs=self.epochs)
        self.model = model
        self.word2index = word2index
        self.label_encoder = le

    def tag(self, x_test):
        x_test_vec = vectorize_titles(
            self.word2index, x_test, save_tokenized=False, save_missed=False
        )
        x_test_vec_padded = pad_sequences(
            x_test_vec, maxlen=self.max_input_length, padding="post", truncating="post"
        )
        return self.model.predict(x_test_vec_padded)

    def evaluate(self, x_test, y_test):

        if not self.model:
            raise Exception("model not trained or not present")

        # Encode the labels, each must be a vector with dim = num. of possible labels
        x_predicted_probs = self.tag(x_test)

        labels_idx = np.argmax(x_predicted_probs, axis=1)
        pred_labels = self.label_encoder.inverse_transform(labels_idx)
        print("\n" + classification_report(y_test, pred_labels))
        report_str = "\n" + classification_report(y_test, pred_labels)
        cm = confusion_matrix(y_test, pred_labels, labels=self.label_encoder.classes_)
        print_cm(cm, labels=self.label_encoder.classes_)
        print()

        misclassifications = []
        for title, pred_y, true_y in zip(x_test, pred_labels, y_test):
            if pred_y != true_y:
                misclassifications.append([title, pred_y, true_y])

        return report_str, misclassifications

    def save(self):
        date_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        joblib.dump(self, f"trained_models/relevancy_clf_{date_time}.pkl")
