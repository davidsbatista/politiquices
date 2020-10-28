"""
A simple Attention Mechanism to be used on top of a Recurrent Layer, e.g.: LSTM, RNN;

adapted from: https://stackoverflow.com/questions/62948332/how-to-add-attention-layer-to-a-bi-lstm/62949137#62949137

https://www.analyticsvidhya.com/blog/2019/11/comprehensive-guide-attention-mechanism-deep-learning/

for visualization: https://stackoverflow.com/questions/53867351/how-to-visualize-attention-weights

"""

import numpy as np
from keras.backend import categorical_crossentropy
from tensorflow.keras.layers import *
from tensorflow.keras.models import *
from tensorflow.keras import backend as K


class attention(Layer):
    def __init__(self, **kwargs):
        super(attention, self).__init__(**kwargs)

    def build(self, input_shape):
        self.W = self.add_weight(name="att_weight",shape=(input_shape[-1],1),initializer="normal")
        self.b = self.add_weight(name="att_bias",shape=(input_shape[1],1),initializer="zeros")
        super(attention, self).build(input_shape)

    def call(self, x, **kwargs):
        et=K.squeeze(K.tanh(K.dot(x,self.W)+self.b),axis=-1)
        at=K.softmax(et)
        at=K.expand_dims(at,axis=-1)
        output=x*at
        return K.sum(output,axis=1)

    def compute_output_shape(self,input_shape):
        return input_shape[0], input_shape[-1]

    def get_config(self):
        return super(attention,self).get_config()


class Attention(Layer):

    def __init__(self, return_sequences=True):
        self.return_sequences = return_sequences
        super(Attention, self).__init__()
        self.W = None
        self.b = None

    def build(self, input_shape):
        self.W = self.add_weight(name="att_weight", shape=(input_shape[-1], 1), initializer="normal")
        self.b = self.add_weight(name="att_bias", shape=(input_shape[1], 1), initializer="zeros")
        super(Attention, self).build(input_shape)

    def call(self, x, **kwargs):
        e = K.tanh(K.dot(x, self.W) + self.b)
        a = K.softmax(e, axis=1)
        output = x * a
        if self.return_sequences:
            return output

        return K.sum(output, axis=1)


def main():

    max_input_length = 100
    max_words = 333
    emb_dim = 100

    """
    i = Input(shape=(max_input_length,), dtype="int32", name="main_input")
    # x = embedding_layer(i)
    x = Embedding(max_words, emb_dim, input_length=max_input_length)(i)
    lstm_out = Bidirectional(LSTM(128, dropout=0.3, recurrent_dropout=0.3, return_sequences=True))(x)
    # o = Dense(self.num_classes, activation="softmax", name="output")(lstm_out)
    attn = Attention(return_sequences=False)(lstm_out)  # receive 3D and output 2D
    o = Dense(1, activation="sigmoid", name="output")(attn)
    model = Model(inputs=i, outputs=o)
    model.compile(
        loss={"output": categorical_crossentropy}, optimizer="adam", metrics=["accuracy"]
    )

    model.summary()

    n_sample = 5
    X = np.random.randint(0, max_words, (n_sample, max_input_length))
    Y = np.random.randint(0, 2, n_sample)

    model.fit(X, Y, epochs=3)

    model = Sequential()
    model.add(Embedding(max_words, emb_dim, input_length=max_len))
    model.add(Bidirectional(LSTM(32, return_sequences=False)))
    model.add(attention(return_sequences=True))  # receive 3D and output 3D
    model.add(LSTM(32))
    model.add(Dense(1, activation='sigmoid'))
    model.summary()

    model.compile('adam', 'binary_crossentropy')
    model.fit(X, Y, epochs=3)
    """

    inputs = Input(shape=(max_input_length,), dtype="int32", name="main_input")
    x = Embedding(input_dim=max_words + 1, output_dim=emb_dim, input_length=max_input_length)(inputs)
    att_in = LSTM(64, return_sequences=True, dropout=0.3, recurrent_dropout=0.2)(x)
    att_out = attention()(att_in)
    outputs = Dense(1, activation='sigmoid', trainable=True)(att_out)
    model = Model(inputs, outputs)
    model.summary()


if __name__ == '__main__':
    main()
