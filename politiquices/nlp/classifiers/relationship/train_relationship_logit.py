import re
from collections import Counter

import spacy
from sklearn.model_selection import StratifiedKFold

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


def main():
    training_data = read_ground_truth("../../../politiquices_training_data.tsv")
    training_data_webapp = read_ground_truth("../../api_annotations/annotations_from_webapp.tsv")
    all_data = training_data + training_data_webapp
    titles, labels = pre_process_train_data(all_data)

    for title in titles:
        print(title)
        # pos_tags = self.get_pos_tags(title)
        # context = self.get_context(title, ent1, ent2)


if __name__ == "__main__":
    main()
