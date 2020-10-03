from politiquices.extraction.classifiers.news_titles.embeddings_utils import get_embeddings
from politiquices.extraction.classifiers.news_titles.relationship_clf import (
    RelationshipClassifier,
    pre_process_train_data,
)
from politiquices.extraction.commons import clean_title, read_ground_truth


def main():
    data = read_ground_truth(only_label=True)

    for entry in data:
        entry["title"] = clean_title(entry["title"]).strip()

    docs, labels = pre_process_train_data(data)
    word2embedding, word2index = get_embeddings()

    """
    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    for train_index, test_index in skf.split(docs, labels):
        x_train = [doc for idx, doc in enumerate(docs) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(docs) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]
        model = RelationshipClassifier(directional=True, epochs=20)
        model.train(x_train, y_train, word2index, word2embedding)
        report = model.evaluate(x_test, y_test)
        print(report)
    """

    model = RelationshipClassifier(directional=True, epochs=20)
    model.train(docs, labels, word2index, word2embedding)
    model.save()


if __name__ == "__main__":
    main()
