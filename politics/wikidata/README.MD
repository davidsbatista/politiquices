

docker network create elastic
docker run --network=elastic --name=elasticsearch -p 9200:9200 -p 9301:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.6.2
docker run --network=elastic -p 5601:5601 docker.elastic.co/kibana/kibana:7.6.2




http://localhost:5601/app/kibana

http://localhost:5601/app/kibana#/discover?_g=(refreshInterval:(pause:!t,value:0),time:(from:now-15m,to:now))

