
.SILENT:


dev:
	@echo "Starting to build the development environment"

	python3 -m venv $${HOME}/politiquices_extraction_venv; . $${HOME}/politiquices_extraction_venv/bin/activate; \
	pip install --upgrade pip > /dev/null; \
	pip install -r requirements.txt > /dev/null; \
	export PYTHONPATH=$HOME/politiquices/; \

	@echo "Development environment setup done to activate run:"
	@echo "\`source ~/politiquices_extraction_venv/bin/activate\`"


lint:
	/Users/dsbatista/virtual_envs/python38/bin/flake8
	# pylint arquivo.pt --rcfile=pylint.cfg
	pylint classifier --rcfile=pylint.cfg
	pylint utils --rcfile=pylint.cfg
	# pylint wikidata --rcfile=pylint.cfg