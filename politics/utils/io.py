import csv


def read_ground_truth(only_label=False):
    data = []
    with open(
            "../../data/annotated/publico_politica.tsv", newline=""
    ) as csvfile:
        titles = csv.reader(csvfile, delimiter="\t", quotechar="|")
        for row in titles:
            sample = {
                "sentence": row[0],
                "label": row[1],
                "date": row[2],
                "url": row[3],
                "ent1": row[4],
                "ent2": row[5],
                "ent1_id": row[6],
                "ent2_id": row[7],
            }
            if only_label:
                if row[1]:
                    data.append(sample)
            else:
                data.append(sample)
    return data

