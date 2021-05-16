import nltk
import pt_core_news_lg

from politiquices.nlp.utils.utils import find_sub_list


class DirectionClassifier:
    """
    use spaCy to extract morphological information

    https://spacy.io/api/morphology
    https://universaldependencies.org/u/pos/index.html

    https://www.linguateca.pt/Floresta/doc/VISLsymbolset-manual.html
    https://www.linguateca.pt/Floresta/index_en.html
    """

    def __init__(self):
        self.nlp = pt_core_news_lg.load(disable=[
                "tok2vec"
                "tagger",
                "lemmatizer",
                "ner",
                "attribute_ruler",
            ])
        passive_voice_mark = """PASSIVE_VOICE: {%s}""" % "<VERB><ADP>"
        self.passive_voice_pattern = nltk.RegexpParser(passive_voice_mark)
        mentioned_at_end = """ENT2_MENTIONED_AT_END_WITH_VERB: {%s}""" % "<PUNCT><VERB|ADP>$"
        self.mentioned_at_end_pattern = nltk.RegexpParser(mentioned_at_end)
        third_pattern = """ENT2_MENTIONED_AT_END_WITH_NOUN: {%s}""" % "<ADJ>?<NOUN><ADJ>?<ADP>$"
        self.third_pattern = nltk.RegexpParser(third_pattern)

    @staticmethod
    def get_contexts(title_pos_tags, ent1, ent2):
        ent1_tokens = ent1.split()
        ent2_tokens = ent2.split()
        title_text = [t[0] for t in title_pos_tags]
        ent1_interval = find_sub_list(ent1_tokens, title_text)
        if ent1_interval:
            ent1_start, ent1_end = ent1_interval
            ent2_interval = find_sub_list(ent2_tokens, title_text)
            if ent2_interval:
                ent2_start, ent2_end = ent2_interval
                bet = title_pos_tags[ent1_end + 1: ent2_start]
                bef = title_pos_tags[:ent1_end]
                aft = title_pos_tags[ent2_end+1:]
                return bef, bet, aft

        return None

    def get_pos_tags(self, sentence):
        doc = self.nlp(sentence)
        morphology = [(t.text, t.pos_, t.morph) for t in doc]
        return morphology, doc

    def detect_direction(self, sentence, ent1, ent2):

        pos_tags, doc = self.get_pos_tags(sentence)
        bef, bet, aft = self.get_contexts(pos_tags, ent1, ent2)

        if not bet:
            print("no context extracted")
            return "ent1_rel_ent2", 'no context', None, pos_tags

        # passive voice detection
        patterns_found = self.passive_voice_pattern.parse(bet)
        ent1_subj = False
        ent2_agent = False
        for t in patterns_found.subtrees():
            if t.label() == "PASSIVE_VOICE":
                elements = list(t)
                if elements[0][2].get("Voice") == ['Pass']:
                    for token in doc:
                        # passive form VERB connected to ent1 by 'acl'
                        if token.text == elements[0][0]:
                            if token.dep_ == 'acl' and token.head.text in ent1:
                                return "ent2_rel_ent1", t.label(), bet, pos_tags

                        # ent1 head is 'nsubj:pass'
                        # ent2 head is 'obl:agent'
                        if token.text in ent1 and token.dep_ in ['nsubj:pass']:
                            ent1_subj = True
                        if token.text in ent2 and token.dep_ == 'obl:agent':
                            ent2_agent = True
                        if ent1_subj and ent2_agent:
                            return "ent2_rel_ent1", t.label(), bet, pos_tags

        # ent2 mentioned at the end of headline, before a verb conjugate in the 3rd person singular
        # of the indicative present, e.g.: <diz|afirma|acusa|rebate|concorda|etc.> <ent2>"
        patterns_found = self.mentioned_at_end_pattern.parse(bet)
        for t in patterns_found.subtrees():
            if t.label() == "ENT2_MENTIONED_AT_END_WITH_VERB":
                elements = list(t)
                if elements[1][2].get("Mood") == ['Ind']:
                    return "ent2_rel_ent1", t.label(), bet, pos_tags

        # <NOUN> <ADJ?> de <ent2>
        valid_nouns = ["críticas", "acusações", "ataques", "ataque", "apoio", "convite"]
        valid_adp = ['de']
        # <NOUN> <ADP> <ent2> <EOS>
        patterns_found = self.third_pattern.parse(bet)
        for t in patterns_found.subtrees():
            if t.label() == "ENT2_MENTIONED_AT_END_WITH_NOUN":
                elements = list(t)
                if elements[0][0] in valid_nouns and elements[1][0] in valid_adp:
                    return "ent2_rel_ent1", t.label(), bet, pos_tags

        # defaults to 'ent1_rel_ent2'
        return "ent1_rel_ent2", 'default', bet, pos_tags

