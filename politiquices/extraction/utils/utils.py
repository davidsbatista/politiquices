import csv
import re

from datetime import datetime
from random import randint
from time import sleep


def just_sleep(upper_bound=3, verbose=False):
    sec = randint(1, upper_bound)
    if verbose:
        print(f"sleeping for {sec} seconds")
    sleep(sec)


def write_iterator_to_file(iter_struct, filename):
    with open(filename, 'wt') as f_out:
        for el in iter_struct:
            f_out.write(str(el) + '\n')


def clean_title_quotes(title):
    if title[0] == '"' and title[-1] == '"':
        title = title[1:-1]
    cleaned_title = re.sub(r'[“”″\']', '"', title)
    return re.sub(r'"{2}', '"', cleaned_title)


def clean_title_re(title):

    title = title.replace('DN Online:', '').strip()

    parts = re.split(r'\s[|–>-]\s', title)

    if len(parts) == 2:

        if len(parts[0]) > len(parts[1]):
            # suffix_rules
            clean = re.sub(r'\s[|–>-]\s.*$', '', title).strip()
            return clean

        elif len(parts[1]) > len(parts[0]):
            # prefix_rules
            clean = re.sub(r'^.*\s[|–>-]\s', '', title).strip()
            return clean

        else:
            raise Exception("Can't figure out where to clean")

    elif len(parts) == 3:
        return max(parts, key=lambda x: len(x))

    return title


def convert_dates(date: str):
    date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime('%Y %b')


def get_time_str():
    return datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")


def load_domains():
    domains = []
    with open('data/domains.txt', 'rt') as f_in:
        for line in f_in:
            if not line.startswith('#') and len(line) > 1:
                domains.append(line.strip('\n'))
    return domains


def read_ground_truth(filename, delimiter='\t', only_label=True):
    data = []
    with open(filename, newline="") as csvfile:
        titles = csv.reader(csvfile, delimiter=delimiter)
        for row in titles:
            if len(row) == 8:
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
            else:
                sample = {
                    "title": row[0],
                    "label": row[1],
                    "date": row[2],
                    "url": row[3],
                    "ent1": row[4],
                    "ent2": row[5],
                }

            if only_label:
                if row[1]:
                    data.append(sample)
            else:
                data.append(sample)
    return data
