import csv
import os

import pt_core_news_sm

MODELS = "trained_models/"
nlp = pt_core_news_sm.load(disable=["tagger", "parser"])


def get_politician_names(filename):
    with open(filename, 'rt') as f_in:
        names = [line.strip() for line in f_in]
    return names


def read_raw_data(filename):
    data = []
    with open(filename, newline="") as csvfile:
        arquivo = csv.reader(csvfile, delimiter="\t", quotechar="|")
        for row in arquivo:
            data.append({"date": row[0], "title": row[1], "url": row[2]})
    return data


def main():
    wiki_data_names = get_politician_names("../names.txt")
    sentences = []
    for filename in os.listdir(""):
        sentences.extend(read_raw_data(filename))

    already_seen = set()
    to_annotate = []
    for sentence in sentences:
        if len(sentence['title']) > 99 or sentence['title'] in already_seen:
            continue
        match = []
        for name in wiki_data_names:
            if len(match) > 1:
                print(sentence['title'])
                if sentence['title'].find(match[0]) > sentence['title'].find(match[1]):
                    match.reverse()
                sentence['entities'] = match
                to_annotate.append(sentence)
                already_seen.add(sentence['title'])
                break

            if sentence['title'].count(name) > 0:
                match.append(name)


if __name__ == '__main__':
    main()