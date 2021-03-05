import json

# load all static generated caching stuff
with open("static/json/all_entities_info.json") as f_in:
    all_entities_info = json.load(f_in)

with open("static/json/all_parties_info.json") as f_in:
    all_parties_info = json.load(f_in)

with open("static/json/party_members.json") as f_in:
    all_parties_members = json.load(f_in)

with open("static/json/wiki_id_info.json") as f_in:
    wiki_id_info = json.load(f_in)

with open("static/json/CHAVE-Publico_94_95.jsonl") as f_in:
    chave_publico = [json.loads(line) for line in f_in]
