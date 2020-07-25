### Classifier
- add publico annotated data in training a title relevancy classifier 
- better/cleaner embeddings
- Classifier API:
    - https://medium.com/@8B_EC/tutorial-serving-machine-learning-models-with-fastapi-in-python-c1a27319c459


### Triple Store
 - Docker: automatically load TTL into dataset in Fuseki 
 - how to get SPARQL results with empty subject for repeated statements, i.e.: image + all offices ?
 - set timeout query on Fuseki 
 - use OR in FILTER to avoid doing two queries: 
        https://stackoverflow.com/questions/30501124/or-in-a-sparql-query

### Web App
    - do layouts 
    - listar todas pessoas
    - listar todos os partidos/organizações
    - listar pessoas com informação incompleta: foto, cargos, etc.
    - clicar numa pessoa: desenvolver mais


### Wikidata / Entity Linking
 - Automate loading with Docker
 - https://elasticsearch-cheatsheet.jolicode.com/
 - Expand knowledge base:
     - politicians -> party to which it belongs
     - bankers
     - political parties
     - add Madeira and Azores regional government politicians
     - add anyone that was/is member of portuguese political party
     - add anyone that was/is member of portuguese public institutions, e.g.: CGD, Banco Portugal
     - guys like: Zeinal Bava, portuguese top managers
     - etc.


### Get data from arquivo.pt
    - get latests titles
        - query keywords ?
        - time period ?
        - was this title already processed?
            - is in some BD ?
            - method to detect duplicate titles: semantically similar
            
        
### Other sources:
    https://www.politicaparatodos.pt/
    http://demo.cratica.org/deputados/


### Documentation
 - Jinga tips: https://jinja.palletsprojects.com/en/2.11.x/templates/#batch