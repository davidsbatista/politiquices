
start:
	docker build -t fuseki-docker fuseki-docker/
	docker run -p 3030:3030 -v $(shell pwd)/triples:/usr/share/data fuseki-docker --file=/usr/share/data/sample.ttl /ds
