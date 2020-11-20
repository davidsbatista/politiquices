import json

from sklearn.model_selection import StratifiedKFold

from politiquices.extraction.classifiers.news_titles.embeddings_utils import get_embeddings
from politiquices.extraction.classifiers.news_titles.relevancy_clf import (
    pre_process_train_data,
    LSTMAtt,
)
from politiquices.extraction.utils import read_ground_truth


def main():
    data_publico = read_ground_truth("../../../../data/annotated/publico_politica.tsv")
    data_arquivo = read_ground_truth("../../../../data/annotated/arquivo.tsv")
    docs, labels = pre_process_train_data(data_publico + data_arquivo)

    print("Loading embeddings...")
    # word2embedding, word2index = get_embeddings(filename='skip_s100_small.txt')
    word2embedding, word2index = get_embeddings()

    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    fold_n = 0
    for train_index, test_index in skf.split(docs, labels):
        x_train = [doc for idx, doc in enumerate(docs) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(docs) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]
        model = LSTMAtt(directional=False, epochs=15)
        keras_model = model.train(x_train, y_train, word2index, word2embedding, x_test, y_test)
        model.save(keras_model, fold=str(fold_n))
        model.model = keras_model
        report_str, misclassifications, correct_classifications = model.evaluate(x_test, y_test)

        other = [(title, json.dumps(scores))
                 for title, pred_y, true_y, scores in correct_classifications
                 if pred_y == "other"]

        relevant = [(title, json.dumps(scores))
                    for title, pred_y, true_y, scores in correct_classifications
                    if pred_y == "relevant"]

        pred_other_true_relevant = []
        pred_relevant_true_other = []

        for title, pred_y, true_y, scores in misclassifications:
            if pred_y == "other":
                if true_y == "relevant":
                    pred_other_true_relevant.append((title, scores))

            elif pred_y == "relevant":
                if true_y == "other":
                    pred_relevant_true_other.append((title, scores))

        with open(f"report_fold_{fold_n}", "wt") as f_out:
            f_out.write(report_str)
            f_out.write("\n\n")
            f_out.write("""PREDICTED: 'other' \t TRUE: 'relevant'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_other_true_relevant, key=lambda x: x[1]["other"]):
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")
            f_out.write("\n\n")
            f_out.write("""PREDICTED: 'relevant' \t TRUE: 'other'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_relevant_true_other, key=lambda x: x[1]["relevant"]):
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")

        with open(f"report_correct_fold_{fold_n}", "wt") as f_out:
            f_out.write("""PREDICTED: 'relevant' \t TRUE: 'relevant'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(relevant):
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")
            f_out.write("\n\n")
            f_out.write("""PREDICTED: 'other' \t TRUE: 'other'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(other):
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")

        fold_n += 1

    model = LSTMAtt(directional=False, epochs=15)
    keras_model = model.train(docs, labels, word2index, word2embedding, None, None)
    model.save(keras_model)


if __name__ == "__main__":
    main()
