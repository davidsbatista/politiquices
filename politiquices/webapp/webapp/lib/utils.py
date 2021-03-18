import re

from politiquices.webapp.webapp.lib.cache import wiki_id_info


def make_https(url):
    return re.sub(r'http://', "https://", url)


def add_icon(r):
    """adds either a arquivo.pt, publico.pt or LINGUATECA"""

    if r["url"].startswith("https://publico.pt"):
        r["link_image"] = "/static/images/114px-Logo_publico.png"
        r["image_width"] = "20"
        r["image_height"] = "20"

    elif r["url"].startswith("https://www.linguateca.pt/CHAVE"):
        r["url"] = r['url'].replace('?', '')
        r["url"] = r['url'].replace('https://www.linguateca.pt/CHAVE', 'chave?q=')
        r["link_image"] = "/static/images/linguateca_logo.png"
        r["image_width"] = "68"
        r["image_height"] = "20"

    else:
        r["link_image"] = "/static/images/color_vertical.svg"
        r["image_width"] = "39.8"
        r["image_height"] = "20"


def per_vs_person_linkable(r):

    ent1_wikid_id = r["ent1_wiki"].split("/")[-1]
    link_one = r["title"].replace(
        r["ent1_str"],
        '<a id="ent_1" href="entity?q=' + ent1_wikid_id + '">' + r["ent1_str"] + "</a>",
    )

    ent2_wikid_id = r["ent2_wiki"].split("/")[-1]
    title_link = link_one.replace(
        r["ent2_str"],
        '<a id="ent_2" href="entity?q=' + ent2_wikid_id + '">' + r["ent2_str"] + "</a>",
    )

    r["title_clickable"] = title_link
    add_icon(r)
    r["link"] = f"""<a href="{r["url"]}" target="_blank" rel="noopener noreferrer">\
                    <img src="{r['link_image']}" width="{r['image_width']}" \
                    height="{r['image_height']}"></a>"""


def clickable_title(r, wiki_id):
    # add link to focus entity
    link_one = r["title"].replace(
        r["focus_ent"], '<a id="ent_1" href="entity?q=' + wiki_id + '">' + r["focus_ent"] + "</a>"
    )
    # add link to other entity page
    title_link = link_one.replace(
        r["other_ent_name"],
        '<a id="ent_2" href=' + r["other_ent_url"] + ">" + r["other_ent_name"] + "</a>",
    )

    r["title_clickable"] = title_link
    add_icon(r)

    r['ent1_wiki'] = 'https://www.wikidata.org/entity/'+wiki_id
    r['ent2_wiki'] = 'https://www.wikidata.org/entity/'+r['other_ent_url'].split('q=')[1]
    r['ent1_str'] = r['focus_ent']
    r['ent2_str'] = r['other_ent_name']

    return r


def get_short_name(e_wiki_id):
    if name := wiki_id_info[e_wiki_id].get('shorter_name', None):
        return name
    return wiki_id_info[e_wiki_id]['name']


def make_json(relationships):
    """
    titles/relationships are sent as JSONs containing:
       - date
       - clickable title
       - link to news article with icon
       - ent1
       - ent2
       - ent1_wiki_id
       - ent2_wiki_id
       - url
    """
    json_data = []

    for r in relationships:
        html_title = f"""{r['title_clickable']}"""
        link = f"""<a href="{r["url"]}" target="_blank" rel="noopener noreferrer">\
                   <img src="{r['link_image']}" width="{r['image_width']}" height="20"></a>"""
        json_data.append({"data": r["date"],
                          "titulo": html_title,
                          "link": link,
                          "url": r["url"],
                          'ent1': r['ent1_str'],
                          'ent2': r['ent2_str'],
                          'ent1_wiki': make_https(r['ent1_wiki']),
                          'ent2_wiki': make_https(r['ent2_wiki'])
                          })

    return json_data


def make_single_json(relationship):
    """
    transform titles/relationships into a json, for bootstrap-table
    """
    link = f"<a href=\"{relationship['url']}\" target=\"_blank\" rel=\"noopener noreferrer\"> " \
           f"<img src=\"{relationship['link_image']}\" width=\"{relationship['image_width']}\" " \
           f"height=\"20\"></a>"

    return {"data": relationship["date"],
            "titulo": f"{relationship['title_clickable']}",
            "link": link,
            "url": relationship["url"],
            'ent1': relationship['ent1_str'],
            'ent2': relationship['ent2_str'],
            'ent1_wiki': make_https(relationship['ent1_wiki']),
            'ent2_wiki': make_https(relationship['ent2_wiki'])}


def get_relationship(relationship):
    opposes_gradient = '#E60001'
    supports_gradient = '#44861E'

    if relationship == "opposes":
        return opposes_gradient, "ent1_opposes_ent2", "opõe-se a"

    if relationship == "supports":
        return supports_gradient, "ent1_supports_ent2", "apoia"

    raise Exception("this should not happen")


def invert_relationship(rel_type):
    rel_only = re.match(r'ent[1-2]_(.*)_ent[1-2]', rel_type).groups()[0]
    if rel_type.endswith("ent2"):
        rel_type_inverted = "ent2_" + rel_only + "_ent1"
    elif rel_type.endswith("ent1"):
        rel_type_inverted = "ent1_" + rel_only + "_ent2"
    else:
        raise Exception("this should not happen")

    return rel_type_inverted


def fill_zero_values(labels, input_freq):
    """
    Make sures that 'input_freq' has as many entries as labels,
    by setting to 0 the every non-existent 'label' in input_freq
    """
    zero_filled_values = [0] * len(labels)
    for idx, label in enumerate(labels):
        if label in input_freq.keys():
            zero_filled_values[idx] = input_freq[label]
    return zero_filled_values


def get_chart_labels_min_max(min_date="1994", max_date="2019"):
    all_years = []
    current_date = int(min_date)
    while current_date <= int(max_date):
        all_years.append(current_date)
        current_date += 1
    return [str(year) for year in all_years]


class Switch(dict):
    def __getitem__(self, item):
        for key in self.keys():
            if item in key:
                return super().__getitem__(key)
        raise KeyError(item)


def determine_heatmap_height(nr_persons):

    switch = Switch({
        range(0, 3): "10%",
        range(3, 5): "15%",
        range(5, 10): "25%",
        range(10, 15): "35%",
        range(15, 20): "40%",
        range(20, 25): "45%",
        range(25, 35): "45%",
        range(35, 40): "60%",
        range(40, 9999): "75%",
    })

    print(nr_persons)
    print(switch[nr_persons])
    print("---\n")

    return switch[nr_persons]


def get_info(wiki_id, all_entities_info, all_parties_info):
    """
    Based on a wiki_id returns the entity info or party info, based on the cached JSON files
    """
    if info := [entry for entry in all_parties_info if entry["wiki_id"] == wiki_id]:
        return info[0], "party"

    if info := [entry for entry in all_entities_info if entry["wiki_id"] == wiki_id]:
        return info[0], "person"
