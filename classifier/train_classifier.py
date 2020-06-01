import csv
import numpy
import joblib

from collections import Counter

from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import classification_report


def collect_training_data():
    data = []
    with open('data/trained_data_political_relationships - extracted_info.tsv', newline='') as csvfile:
        titles = csv.reader(csvfile, delimiter='\t', quotechar='|')
        next(titles)
        for row in titles:
            if row[1]:
                data.append({'sentence': row[0], 'label': row[1]})

        return data


def train_model(data):

    docs = [d['sentence'] for d in data]
    labels = [d['label'] for d in data]

    vectorizer = TfidfVectorizer()
    x_data = vectorizer.fit_transform(docs)

    le = preprocessing.LabelEncoder()
    y_data = le.fit_transform(labels)
    clf = LogisticRegressionCV(cv=2, verbose=0).fit(x_data, y_data)
    return clf, vectorizer, le


def main():
    data = collect_training_data()
    for k, v in Counter(d['label'] for d in data).items():
        print(k, v)
    print(len(data))

    clf, vectorizer, le = train_model(data)

    docs = [d['sentence'] for d in data]
    labels = [d['label'] for d in data]

    predicted_probs = clf.predict_proba(vectorizer.transform(docs))

    print(predicted_probs)
    print(type(predicted_probs))
    print(predicted_probs.shape)

    labels_idx = numpy.argmax(predicted_probs, axis=1)
    pred_labels = le.inverse_transform(labels_idx)

    for sent, label in zip(docs, pred_labels):
        print(sent, '\t', label)

    print(classification_report(labels, pred_labels))

    joblib.dump(clf, 'relationship_clf.joblib')
    joblib.dump(vectorizer, 'vectorizer.joblib')
    joblib.dump(le, 'label_encoder.joblib')


if __name__ == '__main__':
    main()
