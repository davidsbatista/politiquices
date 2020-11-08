import numpy as np
import pt_core_news_sm
from keras.layers import Embedding

from politiquices.extraction.utils import get_time_str

nlp = pt_core_news_sm.load()


def load_fasttext_embeddings(file):
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
        word2embedding, index2word = load_fasttext_embeddings(filename)
    else:
        word2embedding, index2word = load_fasttext_embeddings("skip_s100.txt")
    word2index = {v: k for k, v in index2word.items()}
    word2index["PAD"] = 0
    word2index["UNKNOWN"] = 1
    index2word[0] = "PAD"
    index2word[1] = "UNKNOWN"
    return word2embedding, word2index


def vectorize_titles(word2index, x_train, log=False, save_tokenized=False, save_missed=False):
    # tokenize the sentences and convert into vector indexes
    all_sent_tokens = []
    word_no_vectors = set()
    for doc in nlp.pipe(x_train, disable=["tagger", "parser", "ner"]):
        all_sent_tokens.append([str(t).lower() for t in doc])
        if log:
            print(x_train)
            print([str(t).lower() for t in doc])

    # save tokenized sentences to file, for later analysis
    if save_tokenized:
        with open(f'tokens_{get_time_str()}', 'wt') as f_out:
            for sent_tokens in all_sent_tokens:
                f_out.write(' | '.join(sent_tokens)+'\n')

    x_train_vec = []
    for sent in all_sent_tokens:
        tokens_idx = []
        for tok in sent:
            if tok in word2index:
                tokens_idx.append(word2index[tok])
            else:
                tokens_idx.append(word2index["UNKNOWN"])
                word_no_vectors.add(tok)
        x_train_vec.append(tokens_idx)

    if save_missed and word_no_vectors:
        with open(f'missed_embedding_{get_time_str()}', 'wt') as f_out:
            for token in word_no_vectors:
                f_out.write(token+'\n')
        if log:
            print(word_no_vectors)

    return x_train_vec
