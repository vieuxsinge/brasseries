install:
	virtualenv .venv
	.venv/bin/pip install -r requirements.txt

build:
	./.venv/bin/python scrap.py

publish:
	.venv/bin/ghp-import timeline
	git push origin gh-pages
