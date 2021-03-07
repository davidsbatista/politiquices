build:

	echo "Creating 'elastic' network"
	docker network inspect elastic >/dev/null 2>&1 || docker network create elastic

	echo "Launching ElastiSearch"
	docker stop elasticsearch || true && docker rm elasticsearch || true
	docker run -d --network=elastic --name=elasticsearch -p 9200:9200 -p 9301:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.6.2

	echo "Waiting 10sec before launching Kibana"
	sleep 10s;

	echo "Launching Kibana"
	docker stop kibana || true && docker rm kibana || true
	docker run -d --name=kibana --network=elastic -p 5601:5601 docker.elastic.co/kibana/kibana:7.6.2
	docker inspect --format 0.0.0.0:9200 elasticsearch | xargs wget -q --retry-connrefused --tries=10 --waitretry=10 --spider
	echo "ElasticSearch is up and running!"

	echo "Loading data"
	python index_wikidata_entities.py wiki_ttl/

	echo -e "\nhttp://localhost:5601/app/kibana"

clean:
	# ToDo
