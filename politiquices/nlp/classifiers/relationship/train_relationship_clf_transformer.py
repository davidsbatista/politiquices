# https://towardsdatascience.com/working-with-hugging-face-transformers-and-tf-2-0-89bf35e3555a
import re

import numpy as np
from keras.backend import categorical_crossentropy
from keras.utils import to_categorical
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm

from politiquices.extraction.utils import print_cm
from politiquices.nlp.utils.utils import read_ground_truth
from politiquices.extraction.classifiers.news_titles.models.relationship_clf import pre_process_train_data

from transformers import DistilBertTokenizer, TFDistilBertModel
from transformers import TFDistilBertForSequenceClassification, DistilBertConfig
import tensorflow as tf

distil_bert = "distilbert-base-uncased"

from transformers import T5Tokenizer
from transformers import TFT5ForConditionalGeneration


def classify_with_pre_trained():
    # model = "neuralmind/bert-base-portuguese-cased"

    config = DistilBertConfig(num_labels=3)
    config.output_hidden_states = False
    transformer_model = TFDistilBertForSequenceClassification.from_pretrained(
        distil_bert, config=config
    )[0]

    input_ids = tf.keras.layers.Input(shape=(128,), name="input_token", dtype="int32")
    input_masks_ids = tf.keras.layers.Input(shape=(128,), name="masked_token", dtype="int32")
    X = transformer_model(input_ids, input_masks_ids)
    model = tf.keras.Model(inputs=[input_ids, input_masks_ids], outputs=X)

    return model


def extract_embeddings_for_other_clf():
    distil_bert = "distilbert-base-uncased"

    config = DistilBertConfig(dropout=0.2, attention_dropout=0.2)
    config.output_hidden_states = False
    transformer_model = TFDistilBertModel.from_pretrained(distil_bert, config=config)

    input_ids_in = tf.keras.layers.Input(shape=(25,), name="input_token", dtype="int32")
    input_masks_in = tf.keras.layers.Input(shape=(25,), name="masked_token", dtype="int32")

    embedding_layer = transformer_model(input_ids_in, attention_mask=input_masks_in)[0]
    cls_token = embedding_layer[:, 0, :]
    X = tf.keras.layers.BatchNormalization()(cls_token)
    X = tf.keras.layers.Dense(192, activation="relu")(X)
    X = tf.keras.layers.Dropout(0.2)(X)
    X = tf.keras.layers.Dense(3, activation="softmax")(X)
    model = tf.keras.Model(inputs=[input_ids_in, input_masks_in], outputs=X)

    for layer in model.layers[:3]:
        layer.trainable = False

    return model


def fine_tuning_pretrained_transformer_model():
    # TFDistilBertModel
    # model = distil_bert = 'distilbert-base-uncased'
    # config = DistilBertConfig(dropout=0.2, attention_dropout=0.2)
    # config.output_hidden_states = False
    # transformer_model = TFDistilBertModel.from_pretrained(distil_bert, config=config)

    # TFT5ForConditionalGeneration
    model_name = 'unicamp-dl/ptt5-base-portuguese-vocab'
    transformer_model = TFT5ForConditionalGeneration.from_pretrained(model_name)

    input_ids_in = tf.keras.layers.Input(shape=(21,), name='input_token', dtype='int32')
    input_masks_in = tf.keras.layers.Input(shape=(21,), name='masked_token', dtype='int32')

    embedding_layer = transformer_model(input_ids_in, attention_mask=input_masks_in)[0]
    X = tf.keras.layers.Bidirectional(
        tf.keras.layers.LSTM(50, return_sequences=True, dropout=0.1, recurrent_dropout=0.1))(
        embedding_layer)
    X = tf.keras.layers.GlobalMaxPool1D()(X)
    X = tf.keras.layers.Dense(50, activation='relu')(X)
    X = tf.keras.layers.Dropout(0.2)(X)
    X = tf.keras.layers.Dense(3, activation='sigmoid', name='output')(X)
    model = tf.keras.Model(inputs=[input_ids_in, input_masks_in], outputs=X)

    for layer in model.layers[:3]:
        layer.trainable = False

    return model


def tokenize(sentences, tokenizer):

    input_ids, input_masks, input_segments = [], [], []

    for sentence in tqdm(sentences):
        inputs = tokenizer.encode_plus(
            sentence,
            add_special_tokens=True,
            max_length=25,
            pad_to_max_length=True,
            return_attention_mask=True,
            return_token_type_ids=True,
        )

        input_ids.append(inputs["input_ids"])
        input_masks.append(inputs["attention_mask"])
        input_segments.append(inputs["token_type_ids"])

    return (
        np.asarray(input_ids, dtype="int32"),
        np.asarray(input_masks, dtype="int32"),
        np.asarray(input_segments, dtype="int32"),
    )


def main():
    # Defining DistilBERT tokonizer
    tokenizer = DistilBertTokenizer.from_pretrained(
        distil_bert, do_lower_case=True, add_special_tokens=True, max_length=21,
        pad_to_max_length=True
    )

    model_name = 'unicamp-dl/ptt5-base-portuguese-vocab'
    tokenizer = T5Tokenizer.from_pretrained(model_name)

    f_name = "../../../../data/annotated/publico_politica.tsv"
    data = read_ground_truth(f_name, only_label=True)
    docs, labels = pre_process_train_data(data)
    y_test = [re.sub(r"_?ent[1-2]_?", "", y_sample) for y_sample in labels]

    # tokenize
    train_data = tokenize(docs[0:500], tokenizer)
    train_label = y_test[0:500]

    le = LabelEncoder()
    y_train_encoded = le.fit_transform(train_label)
    y_train_vec = to_categorical(y_train_encoded, num_classes=None)

    model = fine_tuning_pretrained_transformer_model()
    model.compile(
        loss={"output": categorical_crossentropy}, optimizer="adam", metrics=["accuracy"]
    )

    model.fit(train_data, y_train_vec, epochs=10)

    f_name = "model_test_10"
    model.save_weights(f_name)

    test_data = tokenize(docs[500:1000], tokenizer)
    test_label = y_test[500:1000]

    x_predicted_probs = model.predict(test_data)
    labels_idx = np.argmax(x_predicted_probs, axis=1)
    pred_labels = le.inverse_transform(labels_idx)

    print("\n" + classification_report(test_label, pred_labels))
    cm = confusion_matrix(test_label, pred_labels, labels=le.classes_)
    print_cm(cm, labels=le.classes_)
    print()


if __name__ == "__main__":
    main()
