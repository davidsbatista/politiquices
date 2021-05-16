from collections import defaultdict

from sklearn.metrics import classification_report

from politiquices.nlp.classifiers.direction.relationship_direction_clf import DirectionClassifier
from politiquices.nlp.utils.utils import (
    clean_title_quotes,
    clean_title_re,
    read_ground_truth
)


def main():
    all_data = read_ground_truth("../politiquices_data_v1.0.csv")
    direction_clf = DirectionClassifier()
    true_direction = []
    pred_direction = []

    wrong_patterns = defaultdict(int)
    correct_patterns = defaultdict(int)

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
                wrong_patterns[pattern] += 1
                """
                if pattern == "default":
                    print("true: ", true)
                    print("pred: ", pred)
                    print(d["title"])
                    print(context)
                    # print(pos_tags)
                    print("\n-----------------------------")
                """
            elif true == pred:
                correct_patterns[pattern] += 1
                """
                if pattern == 'POTENTIALLY_PASSIVE_VOICE':
                    if true == "ent2_rel_ent1":
                        print("true: ", true)
                        print("pred: ", pred)
                        print(d["title"])
                        print()
                        print(context)
                        print("\n-----------------------------")
                """

    print(classification_report(true_direction, pred_direction))
    print("\nPATTERNS WRONG PREDICTION")
    print("----------------------------")
    for k, v in wrong_patterns.items():
        print(k, v)
    print("\nPATTERNS CORRECT PREDICTION")
    print("----------------------------")
    for k, v in correct_patterns.items():
        print(k, v)


if __name__ == "__main__":
    main()
