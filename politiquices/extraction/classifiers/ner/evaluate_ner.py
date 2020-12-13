import pt_core_news_lg

from politiquices.extraction.utils import read_ground_truth, clean_title_re

nlp = pt_core_news_lg.load(disable=["tagger", "parser"])


def main():
    arquivo = read_ground_truth("../../../../data/annotated/arquivo.tsv")
    publico = read_ground_truth("../../../../data/annotated/publico_politica.tsv")
    tp_total = 0
    fp_total = 0
    fn_total = 0

    for x in arquivo:
        if x['label'] == '':
            continue
        """
        print(x['title'])
        print(x['ent1'])
        print(x['ent2'])
        print()
        """
        tp, fp, fn = evaluate_ner(clean_title_re(x['title']), [x['ent1'], x['ent2']])
        tp_total += tp
        fp_total += fp
        fn_total += fn

    """
    for x in publico:
        tp, fp, fn = evaluate_ner(x['title'], [x['ent1'], x['ent2']])
        tp_total += tp
        fp_total += fp
        fn_total += fn
    """

    print("Precision: ", tp_total / (tp_total + fp_total))
    print("Recall   : ", tp_total / (tp_total + fn_total))


def evaluate_ner(title, truth_person):
    doc = nlp(title)
    pred_persons = [str(ent) for ent in doc.ents if ent.label_ == 'PER']
    tp = 0
    fp = 0
    fn = 0
    for t_ent in truth_person:
        if t_ent in pred_persons:
            tp += 1
        else:
            fn += 1

    for p_ent in pred_persons:
        if p_ent not in truth_person:
            fp += 1

    if pred_persons != truth_person:
        print(title)
        print("TRUTH: ", truth_person)
        print("PRED : ", pred_persons)
        print("TP:", tp)
        print("FP:", fp)
        print("FN:", fn)
        print()

    return tp, fp, fn


if __name__ == '__main__':
    main()
