import json

from sklearn.model_selection import StratifiedKFold

from politiquices.extraction.classifiers.news_titles.embeddings_utils import get_embeddings
from politiquices.extraction.classifiers.news_titles.relationship_clf import (
    RelationshipClassifier,
    pre_process_train_data,
    LSTMAtt)
from politiquices.extraction.utils import read_ground_truth


def main():
    data_publico = read_ground_truth("../../../../data/annotated/publico_politica.tsv",
                                     only_label=True)
    docs, labels = pre_process_train_data(data_publico)
    # data_arquivo = read_ground_truth("../../../../data/annotated/arquivo.tsv", only_label=True)
    # data_webapp = read_ground_truth("../annotations_from_webapp.csv", delimiter=",",
    #                                 only_label=True)
    # docs, labels = pre_process_train_data(data_arquivo+data_publico+data_webapp)
    print("Loading embeddings...")
    word2embedding, word2index = get_embeddings()
    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    fold_n = 0
    for train_index, test_index in skf.split(docs, labels):
        x_train = [doc for idx, doc in enumerate(docs) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(docs) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]
        # model = RelationshipClassifier(directional=True, epochs=1)
        model = LSTMAtt(directional=False, epochs=5)
        model.train(x_train, y_train, word2index, word2embedding, x_test, y_test)
        report_str, misclassifications, correct_classifications = model.evaluate(x_test, y_test)

        supports = [(title, json.dumps(scores))
                    for title, pred_y, true_y, scores in correct_classifications
                    if pred_y == 'supports']

        opposes = [(title, json.dumps(scores))
                   for title, pred_y, true_y, scores in correct_classifications
                   if pred_y == 'opposes']

        other = [(title, json.dumps(scores))
                 for title, pred_y, true_y, scores in correct_classifications
                 if pred_y == 'other']

        pred_oppose_true_support = []
        pred_oppose_true_other = []
        pred_support_true_other = []
        pred_support_true_oppose = []
        pred_other_true_oppose = []
        pred_other_true_support = []

        for title, pred_y, true_y, scores in misclassifications:
            if pred_y == 'opposes':
                if true_y == 'supports':
                    pred_oppose_true_support.append((title, json.dumps(scores)))
                if true_y == 'other':
                    pred_oppose_true_other.append((title, json.dumps(scores)))

            elif pred_y == 'supports':
                if true_y == 'other':
                    pred_support_true_other.append((title, json.dumps(scores)))
                if true_y == 'opposes':
                    pred_support_true_oppose.append((title, json.dumps(scores)))

            elif pred_y == 'other':
                if true_y == 'supports':
                    pred_other_true_support.append((title, json.dumps(scores)))
                if true_y == 'opposes':
                    pred_other_true_oppose.append((title, json.dumps(scores)))

        with open(f'report_fold_{fold_n}', 'wt') as f_out:
            f_out.write(report_str)
            f_out.write('\n\n')
            f_out.write("""PREDICTED: 'opposes' \t TRUE: 'supports'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_oppose_true_support):
                f_out.write(title[0]+'\t'+str(title[1])+'\n\n')
            f_out.write('\n\n')
            f_out.write("""PREDICTED: 'opposes' \t TRUE: 'other'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_oppose_true_other):
                f_out.write(title[0]+'\t'+str(title[1])+'\n\n')
            f_out.write('\n\n')
            f_out.write("""PREDICTED: 'supports' \t TRUE: 'opposes'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_support_true_oppose):
                f_out.write(title[0]+'\t'+str(title[1])+'\n\n')
            f_out.write('\n\n')
            f_out.write("""PREDICTED: 'supports' \t TRUE: 'other'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_support_true_other):
                f_out.write(title[0]+'\t'+str(title[1])+'\n\n')
            f_out.write('\n\n')
            f_out.write("""PREDICTED: 'other' \t TRUE: 'supports'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_other_true_support):
                f_out.write(title[0]+'\t'+str(title[1])+'\n\n')
            f_out.write('\n\n')
            f_out.write("""PREDICTED: 'other' \t TRUE: 'opposes'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_other_true_oppose):
                f_out.write(title[0]+'\t'+str(title[1])+'\n\n')

        with open(f'report_correct_fold_{fold_n}', 'wt') as f_out:
            f_out.write("""PREDICTED: 'supports' \t TRUE: 'supports'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(supports):
                f_out.write(title[0] + '\t' + str(title[1]) + '\n\n')
            f_out.write('\n\n')
            f_out.write("""PREDICTED: 'opposes' \t TRUE: 'opposes'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(opposes):
                f_out.write(title[0] + '\t' + str(title[1]) + '\n\n')
            f_out.write('\n\n')
            f_out.write("""PREDICTED: 'other' \t TRUE: 'other'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(other):
                f_out.write(title[0] + '\t' + str(title[1]) + '\n\n')

        fold_n += 1

    model = RelationshipClassifier(directional=False, epochs=15)
    model.train(docs, labels, word2index, word2embedding)
    model.save()


if __name__ == "__main__":
    main()
