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
                "parser",
                "lemmatizer",
                "ner",
                "attribute_ruler",
            ])
        passive_voice_mark = """POTENTIALLY_PASSIVE_VOICE: {%s}""" % "<VERB><ADP>"
        self.passive_voice_pattern = nltk.RegexpParser(passive_voice_mark)
        mentioned_at_end = """MENTIONED_AT_END: {%s}""" % "<PUNCT><VERB>$"
        self.mentioned_at_end_pattern = nltk.RegexpParser(mentioned_at_end)
        third_pattern = """THIRD_PATTERN: {%s}""" % "<NOUN><ADP>$"
        self.third_pattern = nltk.RegexpParser(third_pattern)

    @staticmethod
    def get_context(title_pos_tags, ent1, ent2):
        ent1_tokens = ent1.split()
        ent2_tokens = ent2.split()
        title_text = [t[0] for t in title_pos_tags]
        ent1_interval = find_sub_list(ent1_tokens, title_text)
        if ent1_interval:
            ent1_start, ent1_end = ent1_interval
            ent2_interval = find_sub_list(ent2_tokens, title_text)
            if ent2_interval:
                ent2_start, ent2_end = ent2_interval
                return title_pos_tags[ent1_end+1: ent2_start]

        return None

    def get_pos_tags(self, sentence):
        doc = self.nlp(sentence)
        return [(t.text, t.pos_, t.morph) for t in doc]

    def detect_direction(self, sentence, ent1, ent2):

        pos_tags = self.get_pos_tags(sentence)
        context = self.get_context(pos_tags, ent1, ent2)

        if not context:
            return "ent1_rel_ent2", None, None, pos_tags

        # the passive voice
        patterns_found = self.passive_voice_pattern.parse(context)
        for t in patterns_found.subtrees():
            if t.label() == "POTENTIALLY_PASSIVE_VOICE":
                elements = list(t)
                if elements[0][2].get("Voice") == ['Pass']:
                    return "ent2_rel_ent1", patterns_found, context, pos_tags

        # a very frequent pattern at the end of the context: ", <diz|afirma|acusa> <ent2>"
        patterns_found = self.mentioned_at_end_pattern.parse(context)
        for t in patterns_found.subtrees():
            if t.label() == "MENTIONED_AT_END":
                elements = list(t)
                if elements[1][2].get("Mood") == ['Ind']:
                    return "ent2_rel_ent1", patterns_found, context, pos_tags

        # another common pattern
        valid_nouns = ["críticas", "acusações", "ataques", "ataque", "apoio", "apelo"]
        patterns_found = self.third_pattern.parse(context)
        for t in patterns_found.subtrees():
            if t.label() == "THIRD_PATTERN":
                elements = list(t)
                if elements[0][0] in valid_nouns:
                    return "ent2_rel_ent1", patterns_found, context, pos_tags

        # defaults to 'ent1_rel_ent2'
        return "ent1_rel_ent2", None, context, pos_tags

