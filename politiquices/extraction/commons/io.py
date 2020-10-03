import csv


def read_ground_truth(only_label=False):
    data = []
    # ToDo: not hardcoded
    with open(
            "../../../data/annotated/publico_politica.tsv", newline=""
    ) as csvfile:
        titles = csv.reader(csvfile, delimiter="\t", quotechar="|")
        for row in titles:
            sample = {
                "title": row[0],
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


def read_raw_data(filename):
    data = []
    with open(filename, newline="") as csvfile:
        arquivo = csv.reader(csvfile, delimiter="\t", quotechar="|")
        for row in arquivo:
            data.append(
                {
                    "title": row[0],
                    "label": row[1],
                    "ent_1": row[2],
                    "ent_2": row[3],
                    "date": row[4],
                    "url": row[5],
                }
            )
    return data
