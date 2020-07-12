
### Classifier
- refactor `apply_clf_batch.py`
- apply new model on already crawled data
- a classifier/method to detect duplicate titles


### Triple Store
 - automatically load TTL into dataset in Fuseki 
 - how to get SPARQL results with empty subject for repeated statements, i.e.: image + all offices ?
 - set timeout query on Fuseki 
 - use OR in FILTER to avoid doing two queries: 
        https://stackoverflow.com/questions/30501124/or-in-a-sparql-query

### Web App
 - do layouts 


### Wikidata / Entity Linking
- Use initial SPARQL queries to get a list of potentials wiki is:
    - politicians
    - bankers
    - political parties
    - etc.
    
- Use this endpoint to get JSON with all the information for each entity:
    - https://www.mediawiki.org/wiki/Wikibase/EntityData
    
- Filter the information by lang: 'pt', 'en', 'de' and index in ElasticSearch

- Evaluate the query 



### Other sources:
    https://www.politicaparatodos.pt/
    http://demo.cratica.org/deputados/

### Documentation
 - Jinga tips: https://jinja.palletsprojects.com/en/2.11.x/templates/#batch