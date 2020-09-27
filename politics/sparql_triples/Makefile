# start docker
# copy TTL file into docker
# run script to load data

# start docker
docker run -v  ~/PycharmProjects/politic-relationships/politics/sparql_triples/fuseki-data/:/staging --name=fuseki -p 3030:3030 stain/jena-fuseki

docker container commit fuseki stackoverflow/jena-fuseki:latest

docker stop fuseki
docker run -p 3030:3030 -it stackoverflow/jena-fuseki ./fuseki-server --config=/config.ttl




/fuseki-server --file=path/to/file /ds : creates an empty, in-memory dataset, then loads the given file in the memory.

https://medium.com/@rrichajalota234/how-to-apache-jena-fuseki-3-x-x-1304dd810f09