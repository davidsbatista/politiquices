from random import randint
from time import sleep


def just_sleep():
    sec = randint(1, 3)
    print(f"sleeping for {sec} seconds")
    sleep(sec)


def write_iterator_to_file(iter_struct, filename):
    with open(filename, 'wt') as f_out:
        for el in iter_struct:
            f_out.write(str(el) + '\n')
