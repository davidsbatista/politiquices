from sklearn.metrics import classification_report

from politiquices.classifiers.rel_direction.relationship_direction_clf import DirectionClassifier
from politiquices.extraction.utils.utils import (
    clean_title_quotes,
    clean_title_re,
    read_ground_truth
)


def main():
    publico = read_ground_truth("../../../data/annotated/publico.csv")
    arquivo = read_ground_truth("../../../data/annotated/arquivo.csv")
    direction_clf = DirectionClassifier()
    true_direction = []
    pred_direction = []

    for d in publico + arquivo:
        if "supports" in d["label"] or "opposes" in d["label"]:
            clean_title = clean_title_quotes(clean_title_re(d['title']))
            ent1 = d["ent1"]
            ent2 = d["ent2"]

            if ent1 not in clean_title or ent2 not in clean_title:
                print("skipped")
                continue

            true = "ent2_rel_ent1" if d["label"].endswith("ent1") else "ent1_rel_ent2"
            true_direction.append(true)
            pred, pattern = direction_clf.detect_direction(clean_title, ent1, ent2)
            pred_direction.append(pred)

            """
            if true != pred:
                print("true: ", true)
                print("pred: ", pred)
                print(d["title"], "\t", d["label"])
                print(pattern)
                print()
                print("\n-----------------------------")
            """

    print(classification_report(true_direction, pred_direction))


if __name__ == "__main__":
    main()
