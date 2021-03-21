import re
from collections import Counter

import spacy
from sklearn.model_selection import StratifiedKFold

from politiquices.nlp.utils.utils import read_ground_truth, find_sub_list
from politiquices.nlp.utils.utils import clean_title_re
from politiquices.nlp.utils.utils import clean_title_quotes

nlp = spacy.load("pt_core_news_lg", disable=[
    "tok2vec"
    "tagger",
    "parser",
    "lemmatizer",
    "ner",
    "attribute_ruler",
])


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


def get_context(title_pos_tags, ent1, ent2):
    ent1_tokens = ent1.split()
    ent2_tokens = ent2.split()
    title_text = [t[0] for t in title_pos_tags]
    ent1_interval = find_sub_list(ent1_tokens, title_text)
    if ent1_interval:
        ent1_start, ent1_end = ent1_interval
        ent2_interval = find_sub_list(ent2_tokens, title_text)
        if ent2_interval:
            ent2_start, ent2_end = ent2_interval
            return title_pos_tags[ent1_end+1: ent2_start]


def get_pos_tags(sentence):
    doc = nlp(sentence)
    return [(t.text, t.pos_, t.morph) for t in doc]


def main():
    training_data = read_ground_truth("../../../politiquices_training_data.tsv")
    training_data_webapp = read_ground_truth("../../api_annotations/annotations_from_webapp.tsv")
    all_data = training_data + training_data_webapp

    for sample in all_data:
        title = sample['title']
        ent1 = sample['ent1']
        ent2 = sample['ent2']
        pos_tags = get_pos_tags(title)
        context = get_context(pos_tags, ent1, ent2)

        print(title)
        print(ent1)
        print(ent2)
        if context is None:
            exit(-1)
        print([t[0] for t in context])
        print("\n\n--------------")


if __name__ == "__main__":
    main()
