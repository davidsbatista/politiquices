import re
import spacy

from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import StratifiedKFold

from politiquices.nlp.classifiers.relationship.models.embeddings_utils import get_embeddings
from politiquices.nlp.classifiers.relationship.models.relationship_clf import RelationshipClassifier
from politiquices.nlp.classifiers.utils.ml_utils import print_cm
from politiquices.nlp.utils.utils import read_ground_truth

spacy_tokenizer = spacy.load("pt_core_news_lg", disable=['parser', 'tagger', 'ner'])


def tokenize(sentences):
    return [[str(t).lower() for t in spacy_tokenizer(sent)] for sent in sentences]


def remap_y_target(y_labels):
    return [re.sub(r"_?ent[1-2]_?", "", y_sample) if y_sample != 'other' else 'other'
            for y_sample in y_labels]


def main():

    all_data = read_ground_truth("../politiquices_data_v1.0.csv")
    labels = remap_y_target([s['label'] for s in all_data])
    skf = StratifiedKFold(n_splits=4, random_state=42, shuffle=True)

    print("Loading embeddings...")
    word2embedding, word2index = get_embeddings()

    all_data_shuffled = []
    all_preds = []
    all_trues = []
    fold_n = 0

    for train_index, test_index in skf.split(all_data, labels):
        x_train = [doc['title'] for idx, doc in enumerate(all_data) if idx in train_index]
        x_test = [doc['title'] for idx, doc in enumerate(all_data) if idx in test_index]
        y_train = [label for idx, label in enumerate(labels) if idx in train_index]
        y_test = [label for idx, label in enumerate(labels) if idx in test_index]

        model = RelationshipClassifier(epochs=10)
        model.train(x_train, y_train, word2index, word2embedding, x_val_tks=x_test, y_val=y_test)

        report_str, misclassifications, correct, pred_labels = model.evaluate(x_test, y_test)

        all_data_shuffled.extend(x_train)
        all_trues.extend(y_test)
        all_preds.extend(pred_labels)

        fold_n += 1

    print("\n\nFINAL REPORT")
    print(classification_report(all_trues, all_preds, zero_division=0.00))
    cm = confusion_matrix(all_trues, all_preds, labels=['opposes', 'other', 'supports'])
    print_cm(cm, labels=['opposes', 'other', 'supports'])
    print()

    """
    model = RelationshipClassifier(epochs=3)
    x_vec = tokenize(titles)
    model.train(x_vec, labels, word2index, word2embedding, x_val_tks=None, y_val=None)
    model.save()
    """


if __name__ == "__main__":
    main()
