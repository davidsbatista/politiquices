### Triple Store

inspired from
https://hub.docker.com/r/stain/jena-fuseki

 - Infrastructure:
    - set timeout query on Fuseki
 - SPARQL queries:
        - how to get SPARQL results with empty subject for repeated statements, i.e.: image + all offices ?
        - use OR in FILTER to avoid doing two queries:
            https://stackoverflow.com/questions/30501124/or-in-a-sparql-query


### Web App
   - do layouts
   - endpoints:
        - listar todas pessoas
        - listar todos os partidos/organizações
        - listar pessoas com informação incompleta: foto, cargos, etc.
   - sugerir para completar:
        - https://www.politicaparatodos.pt/
        - http://demo.cratica.org/deputados/            
   - clicar numa pessoa: desenvolver mais
   - Jinga tips: https://jinja.palletsprojects.com/en/2.11.x/templates/#batch