from politics.utils import read_ground_truth


def replace_contractions(title):
    """
    see: https://blogs.transparent.com/portuguese/contractions-in-portuguese/

    :param title:
    :return:
    """

    # 01. Em
    title = title.replace(" em o ", " no ")
    title = title.replace(" em a ", " na ")
    title = title.replace(" em os ", " nos ")
    title = title.replace(" em as ", " nas ")
    title = title.replace(" em um ", " num ")
    title = title.replace(" em uma ", " numa ")
    title = title.replace(" em uns ", " nuns ")
    title = title.replace(" em umas ", " numas ")

    # 02. De
    title = title.replace(" de o ", " do ")
    title = title.replace(" de a ", " da ",)
    title = title.replace(" de os ", " dos ")
    title = title.replace(" de as ", " das ")

    title = title.replace(" de um ", " dum ")
    title = title.replace(" de uma ", " duma ")
    title = title.replace(" de uns ", " duns ")
    title = title.replace(" de umas", " dumas ")

    title = title.replace(" de este ", " deste ")
    title = title.replace(" de esta ", " desta ")
    title = title.replace(" de estes ", " destes ")
    title = title.replace(" de estas", " destas ")

    title = title.replace(" de esse ", " desse ")
    title = title.replace(" de essa ", " dessa ")
    title = title.replace(" de esses ", " desses ")
    title = title.replace(" de essas ", " dessas ")

    # 03. Por
    title = title.replace(" por o ", " pelo ")
    title = title.replace(" por a ", " pela ")
    title = title.replace(" por os ", " pelos ")
    title = title.replace(" por as ", " pelas ")

    # ToDo: can be two possibilities
    """
    por + os / por + eles = pelos
    por + as / por + elas = pelas
    """

    # 04. A
    title = title.replace(" a o ", " ao ")
    title = title.replace(" a a ", " à ")
    title = title.replace(" a os ", " aos ")
    title = title.replace(" a as ", " às ")

    return title


def main():
    data = read_ground_truth()
    with open("publico_fixed.tsv", 'wt') as f_out:
        for idx, d in enumerate(data):
            replaced = replace_contractions(d["sentence"])
            ent1_replaced = replace_contractions(d["ent1"])
            ent2_replaced = replace_contractions(d["ent2"])
            out_str = str(
                replaced
                + "\t"
                + d["label"]
                + "\t"
                + d["date"]
                + "\t"
                + d["url"]
                + "\t"
                + ent1_replaced
                + "\t"
                + ent2_replaced
                + "\t"
                + d["ent1_id"]
                + "\t"
                + d["ent2_id"]
            )
            f_out.write(out_str+'\n')


if __name__ == "__main__":
    main()
