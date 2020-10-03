import networkx as nx
import pt_core_news_sm
nlp = pt_core_news_sm.load()


def expand_contractions(title):
    """
    see: https://blogs.transparent.com/portuguese/contractions-in-portuguese/

    :param title:
    :return:
    """

    # 01. Em
    title = title.replace(" no ", " em o ")
    title = title.replace(" na ", " em a ")
    title = title.replace(" nos ", " em os ")
    title = title.replace(" nas ", " em as ")
    title = title.replace(" num ", " em um ")
    title = title.replace(" numa ", " em uma ")
    title = title.replace(" nuns ", " em uns ")
    title = title.replace(" numas ", " em umas ")

    # 02. De
    title = title.replace(" do ", " de o ")
    title = title.replace(" da ", " de a ")
    title = title.replace(" dos ", " de os ")
    title = title.replace(" das ", " de as ")

    title = title.replace(" dum ", " de um ")
    title = title.replace(" duma ", " de uma ")
    title = title.replace(" duns ", " de uns ")
    title = title.replace(" dumas", " de umas ")

    title = title.replace(" deste ", " de este ")
    title = title.replace(" desta ", " de esta ")
    title = title.replace(" destes ", " de estes ")
    title = title.replace(" destas", " de estas ")

    title = title.replace(" desse ", " de esse ")
    title = title.replace(" dessa ", " de essa ")
    title = title.replace(" desses ", " de esses ")
    title = title.replace(" dessas ", " dessas ")

    # 03. Por
    title = title.replace(" pelo ", " por o ")
    title = title.replace(" pela ", " por a ")
    title = title.replace(" pelos ", " por os ")
    title = title.replace(" pelas", " por as ")

    # ToDo: can be two possibilities
    """
    por + os / por + eles = pelos
    por + as / por + elas = pelas
    """

    # 04. A
    title = title.replace(" ao ", " a o ")
    title = title.replace(" à ", " a a ")
    title = title.replace(" aos ", " a os ")
    title = title.replace(" às ", " a as ")

    return title


def named_entity(sentence):
    title = expand_contractions(sentence)
    doc = nlp(title)
    ent_per = [ent.text for ent in doc.ents if str(ent.label_) == 'PER']
    return ent_per


def get_head(tokens):
    """Gets the head token of a subtree"""
    if len(tokens) > 1:
        for token in tokens:
            if token.head not in tokens or token.head == token:
                top_token = token
                break
    else:
        top_token = tokens[0]

    return top_token


def extract_syntactic_path(doc, ent1, ent2):
    edges = []
    for token in doc:
        for child in token.children:
            edges.append(("{0}".format(token), "{0}".format(child)))

    graph = nx.Graph(edges)
    try:
        path = nx.shortest_path(graph, source=str(get_head(ent1)), target=str(get_head(ent2)))
    except nx.NetworkXNoPath:
        return []

    return path
