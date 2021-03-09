
.SILENT:


dev:
	python3.8 -m venv $${HOME}/politiquices_extraction_venv; . $${HOME}/politiquices_extraction_venv/bin/activate; \
	pip install --upgrade pip; \
	pip install -r requirements.txt; \
	export PYTHONPATH=$HOME/politiquices/; \

	@echo "Development environment setup done to activate run:"
	@echo "\`source ~/politiquices_extraction_venv/bin/activate\`"
	@echo "run: python -m spacy download pt_core_news_lg"


lint:
	/Users/dsbatista/virtual_envs/python38/bin/flake8
	# pylint arquivo.pt --rcfile=pylint.cfg
	pylint classifier --rcfile=pylint.cfg
	pylint utils --rcfile=pylint.cfg
	# pylint wikidata --rcfile=pylint.cfg
