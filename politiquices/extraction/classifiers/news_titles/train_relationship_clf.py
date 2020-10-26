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
    data_webapp = read_ground_truth("../annotations_from_webapp.csv", delimiter=",",
                                    only_label=True)
    docs, labels = pre_process_train_data(data_arquivo+data_publico+data_webapp)
    word2embedding, word2index = get_embeddings()
    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    fold_n = 0
    for train_index, test_index in skf.split(docs, labels):
        x_train = [doc for idx, doc in enumerate(docs) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(docs) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]
        model = RelationshipClassifier(directional=True, epochs=25)
        model.train(x_train, y_train, word2index, word2embedding)
        report_str, misclassifications = model.evaluate(x_test, y_test)

        with open(f'report_fold_{fold_n}', 'wt') as f_out:
            f_out.write(report_str)
            f_out.write('\n')
            for title, pred_y, true_y in misclassifications:
                f_out.write(title+'\t'+pred_y+'\t'+true_y+'\n')

        fold_n += 1

    exit(-1)

    model = RelationshipClassifier(directional=True, epochs=1)
    model.train(docs, labels, word2index, word2embedding)
    model.save()


if __name__ == "__main__":
    main()
