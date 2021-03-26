import re
from collections import Counter, defaultdict

import nltk
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

    verb = "<ADV>?<AUX|VERB><PART>?<ADV>?"
    word = "<NOUN|ADJ|ADV|DET|ADP>"
    preposition = "<ADP|ADJ>"
    rel_pattern = "( %s (%s* (%s)+ )? )+ " % (verb, word, preposition)
    reverb_mark = '''REVERB_PATTERN: {%s}''' % rel_pattern
    reverb_pattern = nltk.RegexpParser(reverb_mark)

    word_sentiment = WordSentiment()
    contexts = defaultdict(lambda: defaultdict(list))
    verbs = defaultdict(int)
    verbs_lemma = defaultdict(int)

    for sample in all_data:

        title = sample["title"]
        ent1 = sample["ent1"]
        ent2 = sample["ent2"]
        pos_tags = get_pos_tags(title)
        context = get_context(pos_tags, ent1, ent2)

        # to catch errors in training data
        if context is None or len(context) == 0:
            continue

        label = sample['label']

        if label in other_labels:
            label = 'other'
        else:
            label = re.sub(r"_?ent[1-2]_?", "", label)

        contexts['_'.join([t.pos_ for t in context])][label].append(' '.join([t.text for t in context]))

    """
    for x in sorted(verbs_lemma, key=lambda x: verbs_lemma[x], reverse=True):
        print(x, verbs_lemma[x], word_sentiment.get_sentiment(x))
    print(len(verbs_lemma))
    """

    for pos_tags in sorted(contexts, key=lambda x: len(contexts[x]), reverse=True):
        print(pos_tags, "labels->", len(set(contexts[pos_tags])))
        for label in contexts[pos_tags]:
            print(label)
            print("-----")
            for text in sorted(set(contexts[pos_tags][label])):
                print(text)
            print("\n")
        print("\n\n")

    print(len(contexts))

    """
        # Pattern I: PER <verbal expression w/ positive or negative aspect> PER:
        reverb_patterns = []
        context_text_pos = [(t, t.pos_, t.morph) for t in context]
        patterns_found = reverb_pattern.parse(context_text_pos)
        for tokens in patterns_found.subtrees():
            if tokens.label() == "REVERB_PATTERN":
                reverb_patterns.append(list(tokens))

        if len(reverb_patterns) == 1 and len(reverb_patterns[0]) == 1:
            print(sample['label'])
            print(title)
            print(ent1)
            print(ent2)
            print("Pattern I")
            # print(context_text_pos)
            print()
            print(reverb_patterns[0][0])
            raw = reverb_patterns[0][0][0].text
            lemma = reverb_patterns[0][0][0].lemma_
            print(f"{raw}   : ", word_sentiment.get_sentiment(raw))
            print(f"{lemma} : ", word_sentiment.get_sentiment(lemma))
            lemma = reverb_patterns[0][0][0].lemma_
            contexts[lemma] += 1
            print("\n-----------------")

        continue

        if len(context) == 2:
            # Pattern II:
            # PER <VERB> <SCONJ|ADP> PER <expression w/ positive or negative aspect>
            if context[0].pos_ == 'VERB' and (context[1].pos_ == 'SCONJ' or context[1].pos_ == 'ADP'):
                print(sample['label'])
                print(title)
                print(ent1)
                print(ent2)
                print("Pattern II")
                print(context_text_pos)
                print()
                print(context)
                print([(t.text, t.pos_, t.morph) for t in context])
                print("\n-----------------")

            # Pattern III:
            # PER <ADJ> <ADJ|CONJ> PER
            # the expression dominated by an ADJ indicates the positive or negative aspect
            elif context[0].pos_ == 'ADJ' and (context[1].pos_ == 'ADP' or context[1].pos_ == 'SCONJ'):
                print(sample['label'])
                print(title)
                print(ent1)
                print(ent2)
                print("Pattern III")
                print(context_text_pos)
                print()
                print(context)
                print([(t.text, t.pos_, t.morph) for t in context])
                print("\n-----------------")

            else:
                print(sample['label'])
                print(title)
                print(ent1)
                print(ent2)
                print()
                print("WHATS THIS?")
                print(context)
                print([(t.text, t.pos_, t.morph) for t in context])
                print("\n-----------------")
                continue

        # Pattern IV:
        # "PER e PER" - usually other
        if len(context) == 1 and context[0].text == 'e':
            continue
        """


if __name__ == "__main__":
    main()
