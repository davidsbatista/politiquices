import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report


class TestCallback(tf.keras.callbacks.Callback):

    def __init__(self, tb_callback):
        super().__init__()
        self.tb_callback = tb_callback
        self.step_number = 0

    def on_epoch_end(self, epoch, logs=None):
        test_input = "something"
        test_gt = "some ground truth data"
        test_output = self.model.predict(test_input)
        metric1, metric2 = get_metrics(test_gt, test_output)
        items_to_write = {
            "metric1_name": metric1,
            "metric2_name": metric2
        }
        writer = self.tb_callback.writer
        for name, value in items_to_write.items():
            summary = tf.summary.Summary()
            summary_value = summary.value.add()
            summary_value.simple_value = value
            summary_value.tag = name
            writer.add_summary(summary, self.step_number)
            writer.flush()
        self.step_number += 1


class Metrics(tf.keras.callbacks.Callback):

    def __init__(self, *args, **kwargs):
        super(Metrics, self).__init__()
        self.le = kwargs['le']
        self.x = kwargs['val_x']
        self.y = kwargs['val_y']

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
            self.x = self.validation_data[0]
            self.y = self.validation_data[1]

        y_hat = self.model.predict(self.x)
        labels_idx = np.argmax(y_hat, axis=1)
        pred_labels = self.le.inverse_transform(labels_idx)
        true_labels = self.le.inverse_transform(np.argmax(self.y, axis=1))
        report = classification_report(true_labels, pred_labels)
        print(classification_report(true_labels, pred_labels))

