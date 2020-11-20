from collections import defaultdict

from spacy import kb

from politiquices.extraction.utils import read_ground_truth


def main():
    data_publico = read_ground_truth("../../../../data/annotated/publico_politica.tsv")

    string2id = defaultdict(list)
    id2sting = defaultdict(list)

    for d in data_publico:
        if d['ent1_id'] != 'None':
            string2id[d['ent1']].append(d['ent1_id'])
            id2sting[d['ent1_id']].append(d['ent1'])

        if d['ent2_id'] != 'None':
            string2id[d['ent2']].append(d['ent2_id'])
            id2sting[d['ent2_id']].append(d['ent2'])

    for k, v in string2id.items():
        # print(len(v), '->', len(set(v)))
        if len(set(v)) > 1:
            print(k, '\t', set(v))
            print()


if __name__ == '__main__':
    main()
