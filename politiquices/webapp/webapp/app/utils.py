from datetime import datetime


def convert_dates(date: str):
    date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime("%Y %b")


# ToDo: merge this two functions in one
def make_title_linkable(r, wiki_id):

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

    if r["url"].startswith("http://publico.pt"):
        r["link_image"] = "/static/images/114px-Logo_publico.png"
        r["image_width"] = "20"
    else:
        r["link_image"] = "/static/images/color_vertical.svg"
        r["image_width"] = "39.8"


def make_title_linkable_2_entities(r):

    ent1_wikid_id = r["ent1"].split("/")[-1]
    link_one = r["title"].replace(
        r["ent1_str"],
        '<a id="ent_1" href="entity?q=' + ent1_wikid_id + '">' + r["ent1_str"] + "</a>",
    )

    ent2_wikid_id = r["ent2"].split("/")[-1]
    title_link = link_one.replace(
        r["ent2_str"],
        '<a id="ent_2" href="entity?q=' + ent2_wikid_id + '">' + r["ent2_str"] + "</a>",
    )

    r["title_clickable"] = title_link

    if r["url"].startswith("http://publico.pt"):
        r["link_image"] = "/static/images/114px-Logo_publico.png"
        r["image_width"] = "20"

    else:
        r["link_image"] = "/static/images/color_vertical.svg"
        r["image_width"] = "39.8"