# using tips and tricks from:
#	https://stackoverflow.com/questions/48643466/docker-create-network-should-ignore-existing-network/48643576
# 	https://stackoverflow.com/questions/21183088/how-can-i-wait-for-a-docker-container-to-be-up-and-running

.SILENT: build

build:
	echo "Creating 'elastic' network"
	docker network create elastic || true
	echo "Launching ElastiSearch"
	docker run -d --network=elastic --name=elasticsearch -p 9200:9200 -p 9301:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.6.2
	echo "Waiting 10sec before launching Kibana"
	sleep 10s;
	echo "Launching Kibana"
	docker run -d --network=elastic -p 5601:5601 docker.elastic.co/kibana/kibana:7.6.2
	docker inspect --format 0.0.0.0:9200 elasticsearch | xargs wget -q --retry-connrefused --tries=10 --waitretry=10 --spider
	echo "ElasticSearch is up and running!"
	echo "Loading data"
	python create_es_index.py wiki_jsons/

clean:
	# ToDo
