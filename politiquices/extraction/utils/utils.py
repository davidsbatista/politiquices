import re
import csv

from datetime import datetime
from random import randint
from time import sleep


def just_sleep(upper_bound=3, verbose=False):
    sec = randint(1, upper_bound)
    if verbose:
        print(f"sleeping for {sec} seconds")
    sleep(sec)


def write_iterator_to_file(iter_struct, filename):
    with open(filename, "wt") as f_out:
        for el in iter_struct:
            f_out.write(str(el) + "\n")


def clean_title_quotes(title):
    cleaned_title = re.sub(r"[“”″\']", '"', title)
    return re.sub(r'"{2}', '"', cleaned_title)


def clean_title_re(title):
    title = title.replace("DN Online:", "").strip()
    parts = re.split(r"\s[|–>-]\s", title)

    if len(parts) == 2:

        if len(parts[0]) > len(parts[1]):
            # suffix_rules
            clean = re.sub(r"\s[|–>-]\s.*$", "", title).strip()
            return clean

        elif len(parts[1]) > len(parts[0]):
            # prefix_rules
            clean = re.sub(r"^.*\s[|–>-]\s", "", title).strip()
            return clean

        else:
            raise Exception("Can't figure out where to clean")

    elif len(parts) == 3:
        return max(parts, key=lambda x: len(x))

    return title


def get_time_str():
    return datetime.strftime(datetime.now(), "%Y_%m_%d%_%H_%M_%S")


def read_ground_truth(filename, delimiter=","):
    data = []
    with open(filename, newline="") as csv_file:
        titles = csv.reader(csv_file, delimiter=delimiter)
        for row in titles:
            sample = {
                "title": row[0],
                "label": row[1],
                "idiomatic": row[2],
                "date": row[3],
                "url": row[4],
                "ent1": row[5],
                "ent2": row[6],
            }
            # if wiki_id annotations are present
            if len(row) == 9:
                sample.update({"ent1_id": row[7], "ent2_id": row[8]})
            data.append(sample)

    return data


def find_sub_list(entity_tokens, title_tokens):
    # compact and easy solution adapted from:
    # https://stackoverflow.com/questions/17870544/find-starting-and-ending-indices-of-sublist-in-list
    sll = len(entity_tokens)
    for ind in (i for i, e in enumerate(title_tokens) if e == entity_tokens[0]):
        if title_tokens[ind: ind + sll] == entity_tokens:
            return ind, ind + sll - 1
