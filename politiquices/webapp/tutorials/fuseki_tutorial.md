### Indexing Politiquices + Wikidata graphs into a SPARQL engine

This tutorial uses the Apache Jena SPARQL engine with the Fuseki HTTP endpoint.  The graphs will be 
indexed into two distinct endpoints, a query can then use both graphs in the same query through the 
SPARQL `SERVICE` for federated graph query.

#### Download the Docker + data files

    http://www.politiquices.pt/static/tutorial/fuseki-docker.zip
    http://www.politiquices.pt/static/tutorial/politiquices.ttl
    http://www.politiquices.pt/static/tutorial/wikidata_org.ttl.bz2


#### Build the docker image 

    unzip fuseki-docker.zip
    docker build -t fuseki-docker fuseki-docker


##### Copy the TTL files into the data directory and create symbolic links

    cp politiquices_2020-04-18.ttl wikidata_org_2021-03-19.ttl.bz2 fuseki-data/
    ln -s fuseki-data/politiquices_2020-04-18.ttl fuseki-data/politiquices.ttl
    ln -s fuseki-data/wikidata_org_2021-03-19.ttl.bz2 fuseki-data/wikidata_org.ttl.bz2


##### Run the init.sh inside the docker image
	
    docker run -dit -p 127.0.0.1:3030:3030 fuseki-docker /init.sh

This will take a while from 10 to 20 minutes depending on your hardware, the process running inside 
the docker container can be monitored for instance with `docker logs <container_id>` or using third 
party tools like `lazydocker`

After the process finish an endpoint will available on: 

http://0.0.0.0:3030/

Credentials:

```
username: admin
password: admin
```

A set of queries as [example are available](https://github.com/davidsbatista/politiquices/blob/master/politiquices/webapp/tutorials/sparql_queries.md)
which show how to query both graphs.