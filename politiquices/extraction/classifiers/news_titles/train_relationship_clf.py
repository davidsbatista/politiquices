from sklearn.model_selection import StratifiedKFold

from politiquices.extraction.classifiers.news_titles.embeddings_utils import get_embeddings
from politiquices.extraction.classifiers.news_titles.relationship_clf import (
    RelationshipClassifier,
    pre_process_train_data,
)
from politiquices.extraction.utils import read_ground_truth


def main():
    data_arquivo = read_ground_truth("../../../../data/annotated/arquivo.tsv",
                                     only_label=True)
    data_publico = read_ground_truth("../../../../data/annotated/publico_politica.tsv",
                                     only_label=True)
    docs, labels = pre_process_train_data(data_arquivo+data_publico)
    word2embedding, word2index = get_embeddings()
    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    for train_index, test_index in skf.split(docs, labels):
        x_train = [doc for idx, doc in enumerate(docs) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(docs) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]
        model = RelationshipClassifier(directional=True, epochs=10)
        model.train(x_train, y_train, word2index, word2embedding)
        report = model.evaluate(x_test, y_test)
        print(report)

    model = RelationshipClassifier(directional=True, epochs=10)
    model.train(docs, labels, word2index, word2embedding)
    model.save()


if __name__ == "__main__":
    main()