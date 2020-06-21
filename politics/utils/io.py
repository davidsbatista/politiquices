import csv


def read_ground_truth():
    data = []
    with open(
            "../../data/annotated/political_relationships - annotated_publico.tsv", newline=""
    ) as csvfile:
        titles = csv.reader(csvfile, delimiter="\t", quotechar="|")
        next(titles)
        for row in titles:
            data.append(
                {
                    "sentence": row[0],
                    "label": row[1],
                    "ent1": row[5],
                    "ent1_id": row[7],
                    "ent2": row[6],
                    "ent2_id": row[8],
                }
            )
    return data
