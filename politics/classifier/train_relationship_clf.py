from collections import Counter
from datetime import datetime

import regex
import joblib
import numpy as np

from keras import Input, Model
from keras.layers import Bidirectional, Dense, LSTM
from keras.losses import categorical_crossentropy
from keras.utils import to_categorical
from keras_preprocessing.sequence import pad_sequences

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder

from politics.utils import print_cm, read_ground_truth
from politics.classifier.embeddings_utils import (
    create_embeddings_matrix,
    get_embeddings_layer,
    get_embeddings,
    vectorize_titles
)


def pre_process_train_data(data):
    # filter out some classes samples
    ignore = ["other", "ent1_replaces_ent2", "ent2_replaces_ent1", "meet_together"]
    data = [sample for sample in data if sample["label"] not in ignore]

    print("\nSamples per class:")
    for k, v in Counter(d["label"] for d in data).items():
        print(k, "\t", v)
    print("\nTotal nr. messages:\t", len(data))
    print("\n")
    docs = [(d["sentence"], d["ent1"], d["ent2"]) for d in data]
    labels = [d["label"] for d in data]

    # replace entity name by 'PER'
    docs = [d[0].replace(d[1], "PER").replace(d[2], "PER") for d in docs]

    return docs, labels

    """
    for d, l in zip(docs, labels):
        doc = nlp(d[0])
        print(doc.ents)
        print(d[0])
        print(d[1])
        print(d[2])

        if str(doc.ents[0]) == d[1] and str(doc.ents[1]) == d[2]:
            path = extract_syntactic_path(doc, ent1=doc.ents[0], ent2=doc.ents[1])
            print(path)
            print(l)
        else:
            print("NOT THE SAME")
        print("\n---------------------------")
    """


def get_model(embedding_layer, max_input_length, num_classes):
    i = Input(shape=(max_input_length,), dtype="int32", name="main_input")
    x = embedding_layer(i)
    lstm_out = Bidirectional(LSTM(128, dropout=0.3, recurrent_dropout=0.3))(x)
    o = Dense(num_classes, activation="softmax", name="output")(lstm_out)
    model = Model(inputs=i, outputs=o)
    model.compile(loss={"output": categorical_crossentropy}, optimizer="adam", metrics=["accuracy"])

    return model


def train_lstm(
    x_train, y_train, word2index, word2embedding, epochs=20, directional=False, save=False
):
    x_train_vec = vectorize_titles(word2index, x_train)

    # get the max sentence length, needed for padding
    max_input_length = max([len(x) for x in x_train_vec])
    print("Max. sequence length: ", max_input_length)

    # pad all the sequences of indexes to the 'max_input_length'
    x_train_vec_padded = pad_sequences(
        x_train_vec, maxlen=max_input_length, padding="post", truncating="post"
    )

    # Encode the labels, each must be a vector with dim = num. of possible labels
    if directional is False:
        y_train = [regex.sub(r"_?ent[1-2]_?", "", y_sample) for y_sample in y_train]

    le = LabelEncoder()
    y_train_encoded = le.fit_transform(y_train)
    y_train_vec = to_categorical(y_train_encoded, num_classes=None)
    print("Shape of train data tensor:", x_train_vec_padded.shape)
    print("Shape of train label tensor:", y_train_vec.shape)
    num_classes = y_train_vec.shape[1]

    # create the embedding layer
    embeddings_matrix = create_embeddings_matrix(word2embedding, word2index)
    embedding_layer = get_embeddings_layer(embeddings_matrix, max_input_length, trainable=True)
    print("embeddings_matrix: ", embeddings_matrix.shape)

    model = get_model(embedding_layer, max_input_length, num_classes)

    # ToDo: plot loss graphs on train and test
    model.fit(x_train_vec_padded, y_train_vec, epochs=epochs)

    # save model
    if save:
        date_time = datetime.now().strftime("%Y-%m-%d-%H:%m:%s")
        model.save(f"trained_models/relationship_clf_{date_time}.h5")
        joblib.dump(word2index, f"trained_models/relationship_word2index_{date_time}.joblib")
        joblib.dump(le, f"trained_models/relationship_label_encoder_{date_time}.joblib")
        with open("trained_models/relationship_max_input_length", "wt") as f_out:
            f_out.write(str(max_input_length) + "\n")

    return model, le, word2index, max_input_length


def test_model(model, le, word2index, max_input_length, x_test, y_test, directional=False):

    # Encode the labels, each must be a vector with dim = num. of possible labels
    if directional is False:
        y_test = [regex.sub(r"_?ent[1-2]_?", "", y_sample) for y_sample in y_test]

    x_test_vec = vectorize_titles(word2index, x_test)

    x_test_vec_padded = pad_sequences(
        x_test_vec, maxlen=max_input_length, padding="post", truncating="post"
    )

    predicted_probs = model.predict(x_test_vec_padded)
    labels_idx = np.argmax(predicted_probs, axis=1)
    pred_labels = le.inverse_transform(labels_idx)
    print("\n" + classification_report(y_test, pred_labels))
    cm = confusion_matrix(y_test, pred_labels, labels=le.classes_)
    print_cm(cm, labels=le.classes_)
    print()


def main():
    data = read_ground_truth(only_label=True)
    docs, labels = pre_process_train_data(data)
    word2embedding, word2index = get_embeddings()
    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    for train_index, test_index in skf.split(docs, labels):
        x_train = [doc for idx, doc in enumerate(docs) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(docs) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]

        model, le, word2index, max_input_length = train_lstm(
            x_train, y_train, word2index, word2embedding, epochs=25, directional=True
        )
        test_model(model, le, word2index, max_input_length, x_test, y_test, directional=True)

    train_lstm(docs, labels, word2index, word2embedding, epochs=25, directional=True, save=True)


if __name__ == "__main__":
    main()
