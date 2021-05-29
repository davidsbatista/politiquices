import re
from collections import Counter

import spacy
from sklearn.model_selection import StratifiedKFold

from politiquices.nlp.classifiers.relationship.models.embeddings_utils import get_embeddings
from politiquices.nlp.classifiers.relationship.models.relationship_clf import RelationshipClassifier
from politiquices.nlp.utils.utils import read_ground_truth
from politiquices.nlp.utils.utils import clean_title_re
from politiquices.nlp.utils.utils import clean_title_quotes

spacy_tokenizer = spacy.load("pt_core_news_lg", disable=['parser', 'tagger', 'ner'])


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


def tokenize(sentences):
    return [[str(t).lower() for t in spacy_tokenizer(sent)] for sent in sentences]


def remap_y_target(y_labels):
    return [re.sub(r"_?ent[1-2]_?", "", y_sample) if y_sample != 'other' else 'other'
            for y_sample in y_labels]


def main():
    all_data = read_ground_truth("../politiquices_data_v1.0.csv")
    labels = [s['label'] for s in all_data]
    print("Loading embeddings...")
    word2embedding, word2index = get_embeddings()

    skf = StratifiedKFold(n_splits=4, random_state=42, shuffle=True)
    fold_n = 0
    for train_index, test_index in skf.split(all_data, labels):
        x_train = [doc['title'] for idx, doc in enumerate(all_data) if idx in train_index]
        x_test = [doc['title'] for idx, doc in enumerate(all_data) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]

        model = RelationshipClassifier(epochs=10)
        model.train(x_train, y_train, word2index, word2embedding, x_val_tks=x_test, y_val=y_test)

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

    """
    model = RelationshipClassifier(epochs=3)
    x_vec = tokenize(titles)
    model.train(x_vec, labels, word2index, word2embedding, x_val_tks=None, y_val=None)
    model.save()
    """


if __name__ == "__main__":
    main()
