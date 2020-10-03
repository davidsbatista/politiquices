from inspect import signature

import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve

base_dir = "plots/"


def print_cm(cm, labels, hide_zeroes=False, hide_diagonal=False, hide_threshold=None):
    # taken from here: https://gist.github.com/zachguo/10296432
    """pretty print for confusion matrixes"""
    column_width = max([len(x) for x in labels] + [5])  # 5 is value length
    empty_cell = " " * column_width

    # Begin CHANGES
    fst_empty_cell = (column_width - 3) // 2 * " " + "t/p" + (column_width - 3) // 2 * " "

    if len(fst_empty_cell) < len(empty_cell):
        fst_empty_cell = " " * (len(empty_cell) - len(fst_empty_cell)) + fst_empty_cell
    # Print header
    print("    " + fst_empty_cell, end=" ")
    # End CHANGES

    for label in labels:
        print("%{0}s".format(column_width) % label, end=" ")

    print()
    # Print rows
    for i, label1 in enumerate(labels):
        print("    %{0}s".format(column_width) % label1, end=" ")
        for j in range(len(labels)):
            cell = "%{0}.1f".format(column_width) % cm[i, j]
            if hide_zeroes:
                cell = cell if float(cm[i, j]) != 0 else empty_cell
            if hide_diagonal:
                cell = cell if i != j else empty_cell
            if hide_threshold:
                cell = cell if cm[i, j] > hide_threshold else empty_cell
            print(cell, end=" ")
        print()


def plot_precision_recall_vs_threshold(precisions, recalls, thresholds, filename):
    plt.figure(figsize=(10, 8))
    plt.title("Precision and Recall Scores as a function of the decision threshold")
    plt.plot(thresholds, precisions[:-1], "b--", label="Precision")
    plt.plot(thresholds, recalls[:-1], "g-", label="Recall")

    # loc = plticker.MultipleLocator(base=1.0)  # this locator puts ticks at regular intervals
    # plt.xaxis.set_major_locator(loc)

    plt.grid()
    plt.ylabel("Score")
    plt.xlabel("Decision Threshold")
    plt.legend(loc='best')

    with open(base_dir + filename + '.png', 'wb') as f_out:
        plt.savefig(f_out, bbox_inches='tight')
    plt.close()


def plot_precision_recall_curve(predictions_prob, test_y, pos_label, filename):
    precision, recall, thresholds = precision_recall_curve(test_y, predictions_prob[:, 1:],
                                                           pos_label=pos_label)

    # In matplotlib < 1.5, plt.fill_between does not have a 'step' argument

    step_kwargs = ({'step': 'post'}
                   if 'step' in signature(plt.fill_between).parameters
                   else {})
    plt.step(recall, precision, color='b', alpha=0.2, where='post')
    plt.fill_between(recall, precision, alpha=0.2, color='b', **step_kwargs)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.ylim([0.0, 1.05])
    plt.xlim([0.0, 1.0])
    # plt.title('2-class Precision-Recall curve: AP={0:0.2f}'.format(average_precision))
    with open(base_dir + filename + '.png', 'wb') as f_out:
        plt.savefig(f_out)
    plt.close()

    return precision, recall, thresholds
