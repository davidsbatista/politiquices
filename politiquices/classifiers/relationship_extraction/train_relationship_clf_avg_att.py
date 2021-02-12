import re
from collections import Counter

from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold

from politiquices.classifiers.relationship_extraction.models.lstm_with_atten import KerasTextClassifier
from politiquices.extraction.utils.utils import (
    clean_title_quotes,
    clean_title_re,
    read_ground_truth
)


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
        if d["label"] not in other:
            labels.append(d["label"])
            titles.append((clean_title_quotes((clean_title_re(d["title"]))), d["ent1"], d["ent2"]))

    new_labels = [re.sub(r"_?ent[1-2]_?", "", y_sample) for y_sample in labels]

    print("\nSamples per class:")
    for k, v in Counter(new_labels).items():
        print(k, "\t", v)
    print("\nTotal nr. messages:\t", len(titles))
    print("\n")

    # replace entity name by 'PER'
    titles = [d[0].replace(d[1], "PER").replace(d[2], "PER") for d in titles]

    return titles, new_labels


def main():
    data_publico = read_ground_truth("../../../../data/annotated/publico_politica.tsv")
    data_arquivo = read_ground_truth("../../../../data/annotated/arquivo.tsv")
    docs, labels = pre_process_train_data(data_arquivo + data_publico)

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
            emb_dim=50
        )
        kclf.fit(x_train, y_train, X_val=x_test, y_val=y_test, epochs=15, batch_size=16)

        predictions = kclf.encoder.inverse_transform(kclf.predict(x_test))
        print(classification_report(y_test, predictions))

        fold_n += 1

    max_length = max([len(x) for x in docs])
    kclf = KerasTextClassifier(
        input_length=max_length,
        n_classes=len(set(labels)),
        max_words=150000,
        emb_dim=50
    )
    kclf.fit(docs, labels, epochs=15, batch_size=8)
    kclf.save(path="trained_models/relationship_clf")


if __name__ == "__main__":
    main()
