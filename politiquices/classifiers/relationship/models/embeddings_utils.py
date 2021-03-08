import numpy as np
from keras.layers import Embedding


def load_embeddings(file):
    word2embedding = {}
    index2word = {}
    idx = 2
    with open("resources/" + file) as f_in:
        for line in f_in:
            values = line.split()
            word = values[0]

            # some released embeddings contain repeated words
            if word in word2embedding:
                continue

            # and some errors on the vector values
            try:
                coefs = np.asarray(values[1:], dtype="float32")

            except ValueError:
                print(line)
                continue

            word2embedding[word] = coefs
            index2word[idx] = word
            idx += 1

    print("Loaded %s word vectors." % len(word2embedding))

    return word2embedding, index2word


def create_embeddings_matrix(word2embedding, word2index, embedding_dim=100):
    embeddings_matrix = np.random.rand(len(word2embedding) + 2, embedding_dim)
    for word, idx in word2index.items():
        if idx == 0:
            embeddings_matrix[idx] = np.zeros(embedding_dim)
        embedding_vector = word2embedding.get(word)
        if embedding_vector is not None and embedding_vector.shape[0] == embedding_dim:
            embeddings_matrix[idx] = embedding_vector

    print("Matrix shape: {}".format(embeddings_matrix.shape))
    return embeddings_matrix


def get_embeddings_layer(embeddings_matrix, max_len, name="embedding_layer", trainable=False):
    embedding_layer = Embedding(
        input_dim=embeddings_matrix.shape[0],
        output_dim=embeddings_matrix.shape[1],
        input_length=max_len,
        weights=[embeddings_matrix],
        trainable=trainable,
        name=name,
    )
    return embedding_layer


def get_embeddings(filename=None):
    if filename:
        word2embedding, index2word = load_embeddings(filename)
    else:
        word2embedding, index2word = load_embeddings("skip_s100.txt")
    word2index = {v: k for k, v in index2word.items()}
    word2index["PAD"] = 0
    word2index["UNKNOWN"] = 1
    index2word[0] = "PAD"
    index2word[1] = "UNKNOWN"
    return word2embedding, word2index


def vectorize_titles(word2index, sent_tokens):
    word_no_vectors = set()
    x_train_vec = []
    for sent in sent_tokens:
        tokens_idx = []
        for tok in sent:
            if tok in word2index:
                tokens_idx.append(word2index[tok])
            else:
                tokens_idx.append(word2index["UNKNOWN"])
                word_no_vectors.add(tok)
        x_train_vec.append(tokens_idx)

    return x_train_vec
