### Classifier
- remove expanded contractions from publico.pt 
- a classifier/method to detect duplicate titles
- better/cleaner embeddings
- refactor `apply_clf_batch.py`
- apply new model on already crawled data


### Triple Store
 - automatically load TTL into dataset in Fuseki 
 - how to get SPARQL results with empty subject for repeated statements, i.e.: image + all offices ?
 - set timeout query on Fuseki 
 - use OR in FILTER to avoid doing two queries: 
        https://stackoverflow.com/questions/30501124/or-in-a-sparql-query

### Web App
    - do layouts 


### Wikidata / Entity Linking
- https://elasticsearch-cheatsheet.jolicode.com/
- Expand knowledge base:
    - politicians -> party to which it belongs
    - bankers
    - political parties
    - etc.

### Get data from arquivo.pt
    - get latests titles
        - was this title already processed?
        - time period ?
        - query keywords ? 
 
### API - endpoint
   - relationship classifier
   - relevancy classifier
   - wikidata entity linking classifier
 
 
### Other sources:
    https://www.politicaparatodos.pt/
    http://demo.cratica.org/deputados/

### Documentation
 - Jinga tips: https://jinja.palletsprojects.com/en/2.11.x/templates/#batch