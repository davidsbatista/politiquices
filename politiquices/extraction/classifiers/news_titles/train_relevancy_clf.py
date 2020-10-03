
from sklearn.model_selection import StratifiedKFold

from politiquices.extraction.classifiers.news_titles.embeddings_utils import get_embeddings
from politiquices.extraction.classifiers.news_titles.relevancy_clf import RelevancyClassifier
from politiquices.extraction.commons import clean_title
from politiquices.extraction.commons.io import read_raw_data


def main():
    data = read_raw_data("../../../data/annotated/arquivo.tsv")

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

    model = RelevancyClassifier(directional=True, epochs=20)
    model.train(docs, labels, word2index, word2embedding)
    model.save()


if __name__ == "__main__":
    main()
