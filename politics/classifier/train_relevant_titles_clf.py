import csv

from sklearn.model_selection import StratifiedKFold

from politics.classifier.train_relationship_clf import get_embeddings, train_lstm, test_model
from politics.utils import clean_sentence


def read_raw_data(filename):
    data = []
    with open(filename, newline="") as csvfile:
        arquivo = csv.reader(csvfile, delimiter="\t", quotechar="|")
        for row in arquivo:
            data.append({"title": row[0], "label": row[1], "ent_1": row[2], "ent_2": row[3],
                         "date": row[4], "url": row[5]})
    return data


def main():
    data = read_raw_data('../../data/annotated/arquivo_clean.tsv')
    all_pos_titles = set([clean_sentence(x['title']) for x in data if x['label']])
    all_neg_titles = set([clean_sentence(x['title']) for x in data if x['label'] == ''])

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

    # train with all data
    # train_lstm(docs, labels, word2index, word2embedding, epochs=20, directional=False, save=True)


if __name__ == '__main__':
    main()
