import numpy as np
from keras.layers import Embedding


def load_fasttext_embeddings(file, vocabulary=None):
    embeddings_index = {}
    with open('resources/'+file) as f_in:
        for line in f_in:
            values = line.split()
            word = values[0]
            if word not in vocabulary:
                continue
            coefs = np.asarray(values[1:], dtype='float32')
            embeddings_index[word] = coefs
    print('Loaded %s word vectors.' % len(embeddings_index))
    return embeddings_index


def create_embeddings_matrix(embeddings_index, word2index, embedding_dim=100):
    embeddings_matrix = np.random.rand(len(word2index) + 1, embedding_dim)
    for word, idx in word2index.items():
        if idx == 0:
            embeddings_matrix[idx] = np.zeros(embedding_dim)
        embedding_vector = embeddings_index.get(word)
        if embedding_vector is not None:
            embeddings_matrix[idx] = embedding_vector

    print('Matrix shape: {}'.format(embeddings_matrix.shape))
    return embeddings_matrix


def get_embeddings_layer(embeddings_matrix, max_len, name='embedding_layer', trainable=False):
    embedding_layer = Embedding(
        input_dim=embeddings_matrix.shape[0],
        output_dim=embeddings_matrix.shape[1],
        input_length=max_len,
        weights=[embeddings_matrix],
        trainable=trainable,
        name=name)
    return embedding_layer
