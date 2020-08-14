
.SILENT: start

lint:
	/Users/dsbatista/virtual_envs/python38/bin/flake8
	# pylint arquivo.pt --rcfile=pylint.cfg
	pylint classifier --rcfile=pylint.cfg
	# pylint triples --rcfile=pylint.cfg
	pylint utils --rcfile=pylint.cfg
	# pylint webapp --rcfile=pylint.cfg
	# pylint wikidata --rcfile=pylint.cfg

start:
	$(MAKE) -C wikidata build
	$(MAKE) -C service start

api:
	$(MAKE) -C service start