import csv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
async def create_item(item: Item):
    print(item.ent_1.strip(), item.ent1_wiki.strip())
    print(item.ent_2.strip(), item.ent2_wiki.strip())
    print(item.date.strip(), item.title.strip(), item.url.strip())
    print(item.rel_type.strip())
    print()

    with open('annotations_from_webapp.csv', mode='a+') as f_out:
        writer = csv.writer(f_out, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        row = [item.title.strip(), item.rel_type.strip(), item.date.strip(), item.url.strip(),
               item.ent_1.strip(), item.ent_2.strip(), base_url+item.ent1_wiki.strip(),
               base_url+item.ent2_wiki.strip()]

        writer.writerow(row)

    return item
