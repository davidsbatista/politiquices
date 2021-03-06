import re

import requests
from sklearn.metrics import classification_report, confusion_matrix

from politiquices.extraction.utils import read_ground_truth
from politiquices.extraction.utils.utils import clean_title_re
from politiquices.classifiers.utils.ml_utils import print_cm

url = "http://127.0.0.1:8000/relationship"


def main():
    data = read_ground_truth("../../../data/annotated/arquivo.tsv", only_label=True)

    pred = []
    true = []

    for d in data:

        true_label = re.sub(r"_?ent[1-2]_?", "", d['label'])

        if true_label not in ['opposes', 'supports', 'other']:
            continue

        payload = {'news_title': clean_title_re(d['title']), 'person': [d['ent1'], d['ent2']]}
        response = requests.get(url, params=payload)
        response_dict = response.json()
        pred_label = max(response_dict, key=lambda k: response_dict[k])
        pred_score = response_dict[pred_label]

        # classifier might be confused
        if pred_score < 0.5:
            continue

        pred.append(pred_label)
        true.append(true_label)

        if true_label != pred_label:
            print(clean_title_re(d['title']))
            print("ent_1", d['ent1'])
            print("ent_2", d['ent2'])
            print("true: ", true_label)
            print("pred: ", pred_label)

            print("\n-----------")

    print(classification_report(true, pred))
    cm = confusion_matrix(true, pred, labels=['opposes',  'other', 'supports'])
    print_cm(cm, labels=['opposes',  'other', 'supports'])


if __name__ == '__main__':
    main()
