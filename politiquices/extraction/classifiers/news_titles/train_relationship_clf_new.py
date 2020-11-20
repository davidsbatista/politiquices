import json
import re
from collections import Counter

from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold
from politiquices.extraction.classifiers.news_titles.embeddings_utils import get_embeddings
from politiquices.extraction.classifiers.news_titles.lstm_with_atten import KerasTextClassifier
from politiquices.extraction.classifiers.news_titles.relationship_clf import (
    RelationshipClassifier,
    pre_process_train_data,
    LSTMAtt,
)
from politiquices.extraction.utils import read_ground_truth
from politiquices.extraction.utils.utils import clean_title_quotes, clean_title_re


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
        titles.append((clean_title_quotes((clean_title_re(d["title"]))), d["ent1"], d["ent2"]))
        if d["label"] not in other:
            labels.append(d["label"])
        else:
            labels.append("other")

    new_labels = [re.sub(r"_?ent[1-2]_?", "", y_sample) for y_sample in labels]

    print("\nSamples per class:")
    for k, v in Counter(new_labels).items():
        print(k, "\t", v)
    print("\nTotal nr. messages:\t", len(data))
    print("\n")

    # replace entity name by 'PER'
    titles = [d[0].replace(d[1], "PER").replace(d[2], "PER") for d in titles]

    return titles, new_labels


def main():
    data_publico = read_ground_truth(
        "../../../../data/annotated/publico_politica.tsv", only_label=True
    )

    # extract only support
    data_arquivo = read_ground_truth("../../../../data/annotated/arquivo.tsv", only_label=True)
    # arquivo_supports = [x for x in data_arquivo if "supports" in x["label"]]
    docs, labels = pre_process_train_data(data_arquivo + data_publico)

    # print("Loading embeddings...")
    # word2embedding, word2index = get_embeddings(filename='skip_s100_small.txt')
    # word2embedding, word2index = get_embeddings()

    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    fold_n = 0
    for train_index, test_index in skf.split(docs, labels):
        x_train = [doc for idx, doc in enumerate(docs) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(docs) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]

        max_length = max([len(x) for x in x_train])
        kclf = KerasTextClassifier(
            input_length=max_length,
            n_classes=len(set(labels)),
            max_words=15000,
            emb_dim=100
        )
        kclf.fit(x_train, y_train, X_val=x_test, y_val=y_test, epochs=25, batch_size=16)

        predictions = kclf.encoder.inverse_transform(kclf.predict(x_test))
        print(classification_report(y_test, predictions))

        # keras_model = model.train(x_train, y_train, word2index, word2embedding, x_test, y_test)
        # model.save(keras_model, fold=str(fold_n))
        # model.model = keras_model
        # report_str, misclassifications, correct_classifications = model.evaluate(x_test, y_test)

        fold_n += 1

    # model = LSTMAtt(directional=False, epochs=15)
    # keras_model = model.train(docs, labels, word2index, word2embedding, None, None)
    # model.save(keras_model)


if __name__ == "__main__":
    main()
