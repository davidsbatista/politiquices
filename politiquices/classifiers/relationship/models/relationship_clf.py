import joblib
import numpy as np
from datetime import datetime

from keras import Input, Model
from keras.layers import Bidirectional, Dense, LSTM
from keras.utils import to_categorical
from keras_preprocessing.sequence import pad_sequences
from keras.backend import categorical_crossentropy

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

from politiquices.classifiers.utils.ml_utils import print_cm
from politiquices.classifiers.relationship.models.embeddings_utils import (
    create_embeddings_matrix,
    get_embeddings_layer,
    vectorize_titles,
)


class RelationshipClassifier:

    def __init__(self, epochs=20):
        self.epochs = epochs
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

    def train(self, x_train, y_train, word2index, word2embedding, x_val=None, y_val=None):
        x_train_vec = vectorize_titles(word2index, x_train, save_tokenized=False, save_missed=False)
        if x_val:
            x_val_vec = vectorize_titles(word2index, x_val, save_tokenized=False, save_missed=False)

        # get the max sentence length, needed for padding
        self.max_input_length = max([len(x) for x in x_train_vec])
        print("Max. sequence length: ", self.max_input_length)

        # pad all the sequences of indexes to the 'max_input_length'
        x_train_vec_padded = pad_sequences(
            x_train_vec, maxlen=self.max_input_length, padding="post", truncating="post"
        )
        if x_val:
            x_val_vec_padded = pad_sequences(
                x_val_vec, maxlen=self.max_input_length, padding="post", truncating="post"
            )

        # Encode the labels, each must be a vector with dim = num. of possible labels
        le = LabelEncoder()
        y_train_encoded = le.fit_transform(y_train)
        y_train_vec = to_categorical(y_train_encoded, num_classes=None)
        if y_val:
            y_val_encoded = le.transform(y_val)
            y_val_vec = to_categorical(y_val_encoded)

        print("Shape of train data tensor:", x_train_vec_padded.shape)
        print("Shape of train label tensor:", y_train_vec.shape)
        self.num_classes = y_train_vec.shape[1]
        if x_val and y_val:
            print("Shape of val data tensor:", x_val_vec_padded.shape)
            print("Shape of val label tensor:", y_val_vec.shape)

        # create the embedding layer
        embeddings_matrix = create_embeddings_matrix(word2embedding, word2index)
        embedding_layer = get_embeddings_layer(
            embeddings_matrix, self.max_input_length, trainable=True
        )
        print("embeddings_matrix: ", embeddings_matrix.shape)

        model = self.get_model(embedding_layer)
        val_data = None
        if x_val and y_val:
            val_data = (x_val_vec_padded, y_val_vec)

        # ToDo: plot loss graphs on train and test
        # ToDo: add callbacks
        if val_data:
            self.history = model.fit(
                x_train_vec_padded, y_train_vec, validation_data=val_data, epochs=self.epochs
            )
        else:
            self.history = model.fit(
                x_train_vec_padded, y_train_vec, validation_split=0.1, epochs=self.epochs
            )

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
        correct = []
        for title, pred_y, true_y, score in zip(x_test, pred_labels, y_test, scores):
            if pred_y != true_y:
                misclassifications.append([title, pred_y, true_y, score])
            else:
                correct.append([title, pred_y, true_y, score])

        return report_str, misclassifications, correct

    def save(self):
        date_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        joblib.dump(self, f"trained_models/relationship_clf_{date_time}.joblib")
