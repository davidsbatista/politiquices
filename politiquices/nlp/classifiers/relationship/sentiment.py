
class WordSentiment:

    def __init__(self):
        self.word_sentiment = {}
        with open("../../../../resources/oplexicon_v3.0/lexico_v3.0.txt") as f_in:
            for line in f_in.readlines():
                word, pos, sentiment, annotation = line.split(",")
                self.word_sentiment[word] = sentiment

        with open("../../../../resources/SentiLex-PT02/SentiLex-lem-PT02.txt") as f_in:
            for line in f_in.readlines():
                # venerar.PoS=V;
                # TG=HUM:N0:N1;
                # POL:N0=0;
                # POL:N1=1;
                # ANOT=MAN

                try:
                    word_pos, tagger, sentiment, annotation = line.split(";")
                    word, pos = word_pos.split(".")
                    self.word_sentiment[word] = sentiment
                except ValueError:
                    pass
                    # print(line)

    def get_sentiment(self, word, pos=None):
        return self.word_sentiment.get(word, None)
