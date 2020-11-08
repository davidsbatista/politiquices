import nltk
import pt_core_news_sm
from spacy.matcher.matcher import Matcher

from politiquices.extraction.utils import read_ground_truth

nlp = pt_core_news_sm.load()


def is_passive_voice_present(title: str, ent1: str, ent2: str) -> bool:
    # get PoS-tags
    # apply regex to match PoS-tags to detect passive voice
    pass


def main():
    nlp.disable = ["tagger", "parser", "ner"]

    data_publico = read_ground_truth("../../../../data/annotated/publico_politica.tsv",
                                     only_label=True)
    # data_arquivo = read_ground_truth("../../../../data/annotated/arquivo.tsv", only_label=True)
    # data_webapp = read_ground_truth("../annotations_from_webapp.csv", delimiter=",", only_label=True)


    # AUX VERB ADP
    pattern = r'(<VERB>)*(<ADV>)*(<PART>)*(<VERB>)+(<PART>)*'

    """
    diz 	  	 VERB 	 <mv>|V|PR|3S|IND|@FS-STA
    ter 	  	 AUX 	 <aux>|V|INF|@ICL-<ACC
    sido 	  	 AUX 	 <aux>|V|PCP|@ICL-AUX<
    ameaçado  	 VERB 	 <pass>|<mv>|V|PCP|M|S|@ICL-AUX<
    pelo 	  	 ADP 	 PRP|@<ADVL

    pattern = [{'POS': 'VERB', 'OP': '?'},
               {'POS': 'AUX', 'OP': '*'},
               {'POS': 'VERB', 'OP': '*'},
               {'POS': 'ADP', 'OP': '+'}]

    pattern = [{'POS': 'PUNCT', 'OP': '?'},
               {'POS': 'VERB', 'OP': '*'},
               {'POS': 'PROPN', 'OP': '*'}]

    matcher = Matcher(nlp.vocab)
    matcher.add("VP", None, pattern)

    matches = matcher(doc)
    for match_id, start, end in matches:
        matched_span = doc[start:end]
        print(matched_span.text)
        print("=======================")
    """

    """
    verb = "<ADV>*<AUX>*<VERB><PART>*<ADV>*"
    word = "<NOUN|ADJ|ADV|DET|ADP>"
    preposition = "<ADP|ADJ>"
    rel_pattern = "( %s (%s* (%s)+ )? )+ " % (verb, word, preposition)
    grammar_long = '''REL_PHRASE: {%s}''' % rel_pattern
    reverb_pattern = nltk.RegexpParser(grammar_long)
    """

    passive_voice_mark = '''PASSIVE_VOICE: {%s}''' % "<AUX>*<VERB><ADP>*"
    passive_voice_pattern = nltk.RegexpParser(passive_voice_mark)

    for d in data_publico:
        if 'supports' in d['label'] or 'opposes' in d['label']:
            if d['label'].endswith("ent1"):
                print(d['title'], '\t', d['label'])
                doc = nlp(d['title'])
                pos_tags = [(t.text, t.pos_) for t in doc]
                passive_voice_pattern.parse(pos_tags)

                for token in doc:
                    print(token.text, '\t', token.pos_, '\t', token.tag_)
                print("\n--------------------------")


if __name__ == '__main__':
    main()
