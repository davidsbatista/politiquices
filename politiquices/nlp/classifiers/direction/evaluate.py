from sklearn.metrics import classification_report

from politiquices.nlp.classifiers.direction.relationship_direction_clf import DirectionClassifier
from politiquices.nlp.utils.utils import (
    clean_title_quotes,
    clean_title_re,
    read_ground_truth
)


def main():
    training_data = read_ground_truth("../../../politiquices_training_data.tsv")
    training_data_webapp = read_ground_truth("../../api_annotations/annotations_from_webapp.tsv")
    all_data = training_data + training_data_webapp
    direction_clf = DirectionClassifier()
    true_direction = []
    pred_direction = []

    for idx, d in enumerate(all_data):
        if "supports" in d["label"] or "opposes" in d["label"]:
            clean_title = clean_title_quotes(clean_title_re(d['title']))
            ent1 = d["ent1"]
            ent2 = d["ent2"]

            if ent1 not in clean_title or ent2 not in clean_title:
                print("skipped: ", clean_title)
                continue

            true = "ent2_rel_ent1" if d["label"].endswith("ent1") else "ent1_rel_ent2"
            true_direction.append(true)
            pred, pattern, context, pos_tags = direction_clf.detect_direction(clean_title, ent1, ent2)
            pred_direction.append(pred)

            if true != pred:
                print("true: ", true)
                print("pred: ", pred)
                print(d["title"], "\t", d["label"])
                print(context)
                print("\n-----------------------------")

    print(classification_report(true_direction, pred_direction))


if __name__ == "__main__":
    main()
