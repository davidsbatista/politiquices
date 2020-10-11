from collections import Counter

from sklearn.model_selection import StratifiedKFold

from politiquices.extraction.classifiers.news_titles.embeddings_utils import get_embeddings
from politiquices.extraction.classifiers.news_titles.relevancy_clf import RelevancyClassifier
from politiquices.extraction.utils import clean_title
from politiquices.extraction.utils.utils import read_ground_truth


def count_samples(data):

    not_labeled = []
    all_pos_titles = []
    all_neg_titles = []

    for x in data:
        if x['label'] in ['other', 'meet_together', 'ent1_replaces_ent2', 'ent2_replaces_ent1']:
            all_neg_titles.append(x)
            continue

        if x['label'] in ['ent2_opposes_ent1', 'ent1_opposes_ent2',
                          'ent1_supports_ent2', 'ent2_supports_ent1']:
            all_pos_titles.append(x)
            continue

        not_labeled.append(x)

    print("relevant    : ", len(all_pos_titles))
    print("non-relevant: ", len(all_neg_titles))
    print("not labeled : ", len(not_labeled))

    return all_pos_titles, all_neg_titles


def main():
    data_arquivo = read_ground_truth("../../../../data/annotated/arquivo.tsv")
    data_publico = read_ground_truth("../../../../data/annotated/publico_politica.tsv")

    print("\npublico.pt")
    pos_publico, neg_publico = count_samples(data_publico)
    print("\narquivo.pt")
    pos_arquivo, neg_arquivo = count_samples(data_arquivo)

    data = [(x['title'], "relevant") for x in pos_publico + pos_arquivo]
    data.extend([(x['title'], "non-relevant") for x in neg_publico + neg_arquivo])

    docs = [clean_title(x[0]) for x in data]
    labels = [x[1] for x in data]

    print("\nSamples per class:")
    for k, v in Counter(d[1] for d in data).items():
        print(k, "\t", v)
    print("\nTotal nr. messages:\t", len(data))

    word2embedding, word2index = get_embeddings()

    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    for train_index, test_index in skf.split(docs, labels):
        x_train = [doc for idx, doc in enumerate(docs) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(docs) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]
        model = RelevancyClassifier(directional=False, epochs=10)
        model.train(x_train, y_train, word2index, word2embedding)
        report = model.evaluate(x_test, y_test)
        print(report)

    model = RelevancyClassifier(directional=True, epochs=10)
    model.train(docs, labels, word2index, word2embedding)
    model.save()


if __name__ == "__main__":
    main()
