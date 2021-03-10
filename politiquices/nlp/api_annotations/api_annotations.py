import csv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

app = FastAPI()

origins = [
    "https://politiquices.pt",
    "https://www.politiquices.pt",
    "http://localhost",
    "http://localhost:8080",
]

"""
unless this API also runs on HTTPS you need to permanently disable mixed content blocking for the 
current Firefox active profile:
- type "about:config" in the address bar
- find 'security.mixed_content.block_active_content' and set its value to false
"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Item(BaseModel):
    ent_1: str
    ent_2: str
    ent1_wiki: str
    ent2_wiki: str
    date: str
    title: str
    url: str
    rel_type: str


base_url = 'https://www.wikidata.org/wiki/'


@app.post("/annotation/")
async def create_item(item: Item, request: Request):
    client_ip = request.client.host
    print(item.ent_1.strip(), item.ent1_wiki.strip())
    print(item.ent_2.strip(), item.ent2_wiki.strip())
    print(item.date.strip())
    print(item.title.strip())
    print(item.url.strip())
    print(item.rel_type.strip())
    print(client_ip)

    with open('annotations_from_webapp.csv', mode='a+') as f_out:
        writer = csv.writer(f_out, delimiter=',', quoting=csv.QUOTE_MINIMAL)

        row = [item.title.strip(), item.rel_type.strip(), item.date.strip(), item.url.strip(),
               item.ent_1.strip(), item.ent_2.strip(), base_url+item.ent1_wiki.strip(),
               base_url+item.ent2_wiki.strip(), client_ip]

        writer.writerow(row)

    return item
