from collections import defaultdict

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report


class Metrics(tf.keras.callbacks.Callback):

    def __init__(self, *args, **kwargs):
        super(Metrics, self).__init__()
        self.le = kwargs['le']
        self.metrics_at_epoch = defaultdict(dict)

    def set_model(self, model):
        super(Metrics, self).set_model(model)

        """
        # Get the prediction and label tensor placeholders.
        predictions = self.model._feed_outputs[0]
        labels = tf.cast(self.model._feed_targets[0], tf.bool)
        # Create the PR summary OP.
        self.pr_summary = pr_summary.op(name='pr_curve',
                                        predictions=predictions,
                                        labels=labels,
                                        display_name='Precision-Recall Curve')
        """

    def on_epoch_end(self, epoch, logs=None):
        super(Metrics, self).on_epoch_end(epoch, logs)
        if self.validation_data:
            val_x = self.validation_data[0]
            val_y = self.validation_data[1]
        else:
            raise Exception("No validation data defined")

        y_hat = self.model.predict(val_x)
        labels_idx = np.argmax(y_hat, axis=1)
        pred_labels = self.le.inverse_transform(labels_idx)
        true_labels = self.le.inverse_transform(np.argmax(val_y, axis=1))
        report = classification_report(true_labels, pred_labels, output_dict=True)
        for label, metrics in report.items():
            if label in list(self.le.classes_) + ['weighted avg']:
                self.metrics_at_epoch[epoch][label] = metrics
        print(classification_report(true_labels, pred_labels))

