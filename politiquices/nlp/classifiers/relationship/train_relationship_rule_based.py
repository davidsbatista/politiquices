import re
from collections import Counter, defaultdict

import spacy
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold

from politiquices.nlp.classifiers.relationship.sentiment import WordSentiment
from politiquices.nlp.classifiers.utils.ml_utils import print_cm
from politiquices.nlp.utils.utils import (
    read_ground_truth,
    find_sub_list,
    clean_title_quotes,
    clean_title_re,
)

nlp = spacy.load(
    "pt_core_news_lg",
    disable=["tagger", "parser", "ner", "attribute_ruler"],
)

other_labels = [
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


def get_context(title_pos_tags, ent1, ent2):
    ent1_tokens = ent1.split()
    ent2_tokens = ent2.split()
    title_text = [t.text for t in title_pos_tags]
    ent1_interval = find_sub_list(ent1_tokens, title_text)
    if ent1_interval:
        ent1_start, ent1_end = ent1_interval
        ent2_interval = find_sub_list(ent2_tokens, title_text)
        if ent2_interval:
            ent2_start, ent2_end = ent2_interval
            return title_pos_tags[ent1_end + 1: ent2_start]


def get_pos_tags(sentence):
    doc = nlp(sentence)
    return [t for t in doc]


def main():
    training_data = read_ground_truth("../../../politiquices_training_data.tsv")
    training_data_webapp = read_ground_truth("../../api_annotations/annotations_from_webapp.tsv")
    all_data = training_data + training_data_webapp

    word_sentiment = WordSentiment()
    contexts = defaultdict(int)

    other = ['e', ',']
    supports = ['apoiar', 'convidar', 'elogiar', 'confiança', 'felicitar']
    opposes = ['acusar', 'criticar', 'responsabilizar', 'desmentir', 'atacar', 'contrariar']

    true_labels = []
    pred_labels = []

    for sample in all_data:

        if sample['label'] in other_labels:
            true_labels.append('other')
        else:
            true_labels.append(re.sub(r"_?ent[1-2]_?", "", sample['label']))

        title = sample["title"]
        ent1 = sample["ent1"]
        ent2 = sample["ent2"]
        pos_tags = get_pos_tags(title)
        context = get_context(pos_tags, ent1, ent2)

        if context is None:
            exit(-1)

        # print([(t.text, t.pos_, t.morph) for t in context])
        # print([t.text for t in context if t.pos_ == 'ADJ'])

        context_text = ' '.join([t.lemma_ for t in context])
        contexts[context_text] += 1

        pred_label = 'other'
        if any(x == context for x in other):
            pred_label = 'other'
        elif any(x in context_text for x in supports):
            pred_label = 'supports'
        elif any(x in context_text for x in opposes):
            pred_label = 'opposes'

        pred_labels.append(pred_label)

        """
        if ' '.join([t.text for t in context]) == '':
            print(title)
            print(ent1)
            print(ent2)
            print()
            print(sample['label'])
            print("\n\n--------------")
        """

        """
        for t in context:
            if t.pos_ in ['ADP']:
                continue
            print(t.text, t.pos_, t.lemma_, '\t', word_sentiment.get_sentiment(t.lemma_))
        """

    for x in sorted(contexts, key=lambda x: contexts[x], reverse=True):
        print(x, contexts[x])

    print()

    print(classification_report(true_labels, pred_labels, zero_division=0.00))
    cm = confusion_matrix(true_labels, pred_labels, labels=['opposes', 'other', 'supports'])
    print_cm(cm, labels=['opposes', 'other', 'supports'])
    print()


if __name__ == "__main__":
    main()
