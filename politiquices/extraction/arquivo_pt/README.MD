### Arquivo.PT
 
1. Get a list of all the persons/entities in Knowledge Base which will be use dit as the base 
   for querying Arquivo.pt API:


    python fetch_query_names.py
    
  which will generate the following file:
  
    data/entities_names.txt
  

2. From a list of domains (`data/domains.txt`) get the date from the first crawl and the 
   last crawl of that domain: 


    ptyhon fetch_crawl_dates.py
    

  which will generate the following file:

    data/domains_crawled_dates.json


3. From a list of domains and crawl dates (`data/domains.txt`, `domains_crawled_dates.json`) and
   from a list of persons/entities (`data/entities_names.txt`), query arquivo.pt API and collect
   the news titles:


    ptyhon fetch_news_titles.py

   this will store the results for each entity as `<entity_name>_wikidata_ID.tsv` containing the 
   following fields:
   
    {"title": <title of the news artile>,
     "linkToArchive": <url for arquivo.pt containing the news article>, 
     "tstamp": <time stamp of the crawl data>}


ToDo:
   - method to detect duplicate titles: semantically similar 