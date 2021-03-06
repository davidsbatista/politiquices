import json
from datetime import datetime

import matplotlib.pyplot as plt


def plot_loss_acc(history, fold_nr=None):

    date_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    if fold_nr:
        f_name = f'_{str(fold_nr)}_{date_time}'
    else:
        f_name = f'_{date_time}'

    # summarize history for accuracy
    plt.plot(history.history['accuracy'])
    plt.plot(history.history['val_accuracy'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.savefig('accuracy_'+f_name+'.png')

    # summarize history for loss
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.savefig('loss_'+f_name+'.png')


def plot_metrics(metrics_values, fold_nr=None):

    date_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    if fold_nr:
        f_name = f'metrics_values_{str(fold_nr)}_{date_time}'
    else:
        f_name = f'metrics_values_{date_time}'

    with open(f_name+'.txt', 'wt') as f_out:
        json.dump(metrics_values, f_out, indent=4)

    opposes_precision = []
    opposes_recall = []

    other_precision = []
    other_recall = []

    supports_precision = []
    supports_recall = []

    for epoch, values in metrics_values.items():
        for label, metric_values in values.items():

            if label == 'opposes':
                opposes_precision.append(metric_values['precision'])
                opposes_recall.append(metric_values['recall'])

            if label == 'supports':
                supports_precision.append(metric_values['precision'])
                supports_recall.append(metric_values['recall'])

            if label == 'other':
                other_precision.append(metric_values['precision'])
                other_recall.append(metric_values['recall'])

    # summarize history for loss
    plt.plot(opposes_precision)
    plt.plot(opposes_recall)
    plt.plot(supports_precision)
    plt.plot(supports_recall)
    plt.plot(other_precision)
    plt.plot(other_recall)
    plt.title('Precision/Recall')
    plt.ylabel('Precision-Recall')
    plt.xlabel('epoch')
    plt.legend(['Opposes-Precision', 'Opposes-Recall', 'Supports-Precision', 'Supports-Recall',
                'Other-Precision', 'Other-Recall'], loc='upper left')

    plt.savefig(f_name+'.png')