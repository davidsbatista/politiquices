### Arquivo.PT
 
1. Retrieve a list entities from the Knowledge Base which will be used as input for querying Arquivo.pt API:
   
   `python fetch_query_names.py` 
   
   generating: `data/entities_names.txt`

   NOTE: make sure the Elastic Search with the KB instance is running

2. From a list of domains (`data/domains.txt`) get the date from the first and crawl for each domain: 

   `ptyhon fetch_crawl_dates.py`

   generating: `data/domains_crawled_dates.json`


3. From a list of domains (`data/domains.txt`) and associated crawl dates (`domains_crawled_dates.json`) 
   and a list of persons/entities (`data/entities_names.txt`), query arquivo.pt and collect news 
   titles:
   
   `ptyhon fetch_news_titles.py`

   this will store the results for each entity as `<entity_name>_wikidata_ID.tsv` containing the 
   following fields:

   ```
    {
      "title": <title of the news artile>,
      "linkToArchive": <url for arquivo.pt containing the news article>,
      "tstamp": <time stamp of the crawl data>
    }
   ```