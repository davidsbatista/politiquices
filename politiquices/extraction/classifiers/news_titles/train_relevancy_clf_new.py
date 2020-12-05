from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold

from politiquices.extraction.classifiers.news_titles.relevancy_clf import pre_process_train_data
from politiquices.extraction.utils import read_ground_truth

from lstm_with_atten import KerasTextClassifier


def main():
    data_publico = read_ground_truth("../../../../data/annotated/publico_politica.tsv")
    data_arquivo = read_ground_truth("../../../../data/annotated/arquivo.tsv")
    docs, labels = pre_process_train_data(data_publico + data_arquivo)

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
        kclf.fit(x_train, y_train, X_val=x_test, y_val=y_test, epochs=15, batch_size=8)

        predictions = kclf.encoder.inverse_transform(kclf.predict(x_test))
        print(classification_report(y_test, predictions))

    max_length = max([len(x) for x in docs])
    kclf = KerasTextClassifier(
        input_length=max_length,
        n_classes=len(set(labels)),
        max_words=150000,
        emb_dim=50
    )
    kclf.fit(docs, labels, epochs=15, batch_size=8)
    kclf.save(path="trained_models/relevancy_clf")


if __name__ == "__main__":
    main()
