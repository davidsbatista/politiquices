import csv

from sklearn.model_selection import StratifiedKFold

from politics.classifier.train_classifier import get_embeddings, train_lstm, test_model
from politics.utils import clean_sentence


def read_raw_data(filename):
    data = []
    with open(filename, newline="") as csvfile:
        arquivo = csv.reader(csvfile, delimiter="\t", quotechar="|")
        for row in arquivo:
            data.append({"title": row[0], "ent_1": row[1], "ent_2": row[2],
                         "date": row[3], "url": row[4]})
    return data


def main():
    raw = read_raw_data('../../data/to_annotate.csv')
    pos = read_raw_data('../../data/annotated/arquivo_clean.tsv')

    all_pos_titles = set([clean_sentence(x['title']) for x in pos])
    all_neg_titles = set([clean_sentence(x['title']) for x in raw
                          if clean_sentence(x['title']) not in all_pos_titles])
    data = [(x, 'relevant') for x in all_pos_titles]
    data.extend([(x, 'non-relevant') for x in all_neg_titles])
    docs = [x[0] for x in data]
    labels = [x[1] for x in data]

    word2embedding, word2index = get_embeddings()

    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    for train_index, test_index in skf.split(docs, labels):
        x_train = [doc for idx, doc in enumerate(docs) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(docs) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]

        model, le, word2index, max_input_length = train_lstm(
            x_train, y_train, word2index, word2embedding, epochs=25, directional=False
        )
        test_model(model, le, word2index, max_input_length, x_test, y_test, directional=False)


if __name__ == '__main__':
    main()
