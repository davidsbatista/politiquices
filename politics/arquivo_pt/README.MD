### Arquivo.PT
    TODO:
  - stored all processed data in JSON into a ElasticSearch, maybe Mongo...
  - get latest titles:
      - time period ?
  - method to detect duplicate titles: semantically similar


- Read all persons in Knowledge base and use as the list of persons for use in query
- Use the whole time period: 1996 until today


1. Get a list of all entities to be used in query

    fetch_query_names.py
    
2. Generate a list of domains 1st and last crawled time for 

    fetch_crawl_dates.py
    
3. 