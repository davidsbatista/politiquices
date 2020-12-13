import pt_core_news_lg
from sklearn.metrics import classification_report

from politiquices.extraction.classifiers.news_titles.relationship_direction_clf import detect_direction
from politiquices.extraction.utils.utils import (
    clean_title_quotes,
    clean_title_re,
    read_ground_truth
)


def main():
    nlp = pt_core_news_lg.load()
    nlp.disable = ["tagger", "parser", "ner"]

    data_publico = read_ground_truth("../../../../data/annotated/publico_politica.tsv", only_label=True)
    data_arquivo = read_ground_truth("../../../../data/annotated/arquivo.tsv", only_label=True)
    data_webapp = read_ground_truth("../annotations_from_webapp.csv", delimiter=",", only_label=True)

    true_direction = []
    pred_direction = []

    for d in data_publico + data_arquivo + data_webapp:
        if "supports" in d["label"] or "opposes" in d["label"]:

            clean_title = clean_title_quotes(clean_title_re(d['title']))
            doc = nlp(clean_title)
            ent1 = d["ent1"]
            ent2 = d["ent2"]

            if ent1 not in clean_title or ent2 not in clean_title:
                print("skipped")
                continue

            if d["label"].endswith("ent1"):
                true_direction.append("ent2")
                true = "ent2"
            else:
                true_direction.append("ent1")
                true = "ent1"

            pos_tags = [(t.text, t.pos_, t.tag_) for t in doc]
            pred, pattern = detect_direction(pos_tags, ent1, ent2)
            pred_direction.append(pred)

            if true != pred:
                print("true: ", true)
                print("pred: ", pred)
                print(d["title"], "\t", d["label"])
                print(pos_tags)
                print(pattern)
                print()
                print("\n-----------------------------")

    print(classification_report(true_direction, pred_direction))


if __name__ == "__main__":
    main()
