import re
from collections import Counter

from sklearn.model_selection import StratifiedKFold

from politiquices.classifiers.relationship_extraction.models.embeddings_utils import get_embeddings
from politiquices.classifiers.relationship_extraction.models.relationship_clf import RelationshipClassifier
from politiquices.extraction.utils.utils import read_ground_truth
from politiquices.extraction.utils.utils import clean_title_re
from politiquices.extraction.utils.utils import clean_title_quotes


def pre_process_train_data(data):
    other = [
        "ent1_asks_support_ent2",
        "ent2_asks_support_ent1",
        "ent1_asks_action_ent2",
        "ent1_replaces_ent2",
        "ent2_replaces_ent1",
        "mutual_disagreement",
        "mutual_agreement",
        "more_entities",
        "meet_together",
        "other",
    ]

    titles = []
    labels = []

    for d in data:
        titles.append((clean_title_quotes((clean_title_re(d["title"]))), d["ent1"], d["ent2"]))
        if d["label"] not in other:
            labels.append(d["label"])
        else:
            labels.append('other')

    y_train = [re.sub(r"_?ent[1-2]_?", "", y_sample) for y_sample in labels]
    print("\nSamples per class:")
    for k, v in Counter(y_train).items():
        print(k, "\t", v)
    print("\nTotal nr. messages:\t", len(y_train))
    print("\n")

    # replace entity name by 'PER'
    titles = [d[0].replace(d[1], "PER").replace(d[2], "PER") for d in titles]

    return titles, y_train


def main():
    data_publico = read_ground_truth("../../../../data/annotated/publico_politica.tsv")
    data_arquivo = read_ground_truth("../../../../data/annotated/arquivo.tsv")
    data_webapp = read_ground_truth("../../../../data/annotated/annotations_from_webapp.csv",
                                    delimiter=",")

    titles, labels = pre_process_train_data(data_publico + data_arquivo + data_webapp)

    print("Loading embeddings...")
    word2embedding, word2index = get_embeddings()

    skf = StratifiedKFold(n_splits=2, random_state=42, shuffle=True)
    fold_n = 0
    for train_index, test_index in skf.split(titles, labels):
        x_train = [doc for idx, doc in enumerate(titles) if idx in train_index]
        x_test = [doc for idx, doc in enumerate(titles) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]
        model = RelationshipClassifier(epochs=15)
        model.train(x_train, y_train, word2index, word2embedding, x_val=x_test, y_val=y_test)

        report_str, misclassifications, correct = model.evaluate(x_test, y_test)
        pred_oppose_true_support = []
        pred_oppose_true_other = []
        pred_support_true_other = []
        pred_support_true_oppose = []
        pred_other_true_oppose = []
        pred_other_true_support = []

        for entry in misclassifications:
            title, pred_y, true_y, scores = entry
            if pred_y == "opposes":
                if true_y == "supports":
                    pred_oppose_true_support.append((title, scores))
                if true_y == "other":
                    pred_oppose_true_other.append((title, scores))

            elif pred_y == "supports":
                if true_y == "other":
                    pred_support_true_other.append((title, scores))
                if true_y == "opposes":
                    pred_support_true_oppose.append((title, scores))

            elif pred_y == "other":
                if true_y == "supports":
                    pred_other_true_support.append((title, scores))
                if true_y == "opposes":
                    pred_other_true_oppose.append((title, scores))

        with open(f"report_fold_{fold_n}", "wt") as f_out:
            f_out.write(report_str)
            f_out.write("\n\n")
            f_out.write("""PREDICTED: 'opposes' \t TRUE: 'supports'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_oppose_true_support, key=lambda x: x[1]["opposes"]):
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")
            f_out.write("\n\n")
            f_out.write("""PREDICTED: 'opposes' \t TRUE: 'other'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_oppose_true_other, key=lambda x: x[1]["opposes"]):
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")
            f_out.write("\n\n")
            f_out.write("""PREDICTED: 'supports' \t TRUE: 'opposes'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_support_true_oppose, key=lambda x: x[1]["supports"]):
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")
            f_out.write("\n\n")
            f_out.write("""PREDICTED: 'supports' \t TRUE: 'other'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_support_true_other, key=lambda x: x[1]["supports"]):
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")
            f_out.write("\n\n")
            f_out.write("""PREDICTED: 'other' \t TRUE: 'supports'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_other_true_support, key=lambda x: x[1]["other"]):
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")
            f_out.write("\n\n")
            f_out.write("""PREDICTED: 'other' \t TRUE: 'opposes'\n""")
            f_out.write("--------------------------------------------\n")
            for title in sorted(pred_other_true_oppose, key=lambda x: x[1]["other"]):
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")

        other = []
        opposes = []
        supports = []

        for entry in correct:
            title, pred_y, true_y, scores = entry
            if true_y == 'supports':
                supports.append((title, scores))
            elif true_y == 'opposes':
                opposes.append((title, scores))
            elif true_y == 'other':
                other.append((title, scores))

        with open(f"report_correct_fold_{fold_n}", "wt") as f_out:
            f_out.write("""PREDICTED: 'supports' \t TRUE: 'supports'\n""")
            f_out.write("--------------------------------------------\n")
            for title in supports:
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")
            f_out.write("\n\n")
            f_out.write("""PREDICTED: 'opposes' \t TRUE: 'opposes'\n""")
            f_out.write("--------------------------------------------\n")
            for title in opposes:
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")
            f_out.write("\n\n")
            f_out.write("""PREDICTED: 'other' \t TRUE: 'other'\n""")
            f_out.write("--------------------------------------------\n")
            for title in other:
                f_out.write(title[0] + "\t" + str(title[1]) + "\n\n")

        fold_n += 1

    model = RelationshipClassifier(epochs=15)
    model.train(titles, labels, word2index, word2embedding, x_val=None, y_val=None)
    model.save()


if __name__ == "__main__":
    main()
