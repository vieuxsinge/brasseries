install:
	virtualenv .venv
	.venv/bin/pip install -r requirements.txt

build:
	./.venv/bin/python scrap.py

build-evolution:
	./.venv/bin/python scrap.py graph

publish:
	.venv/bin/ghp-import timeline
	git push origin gh-pages
