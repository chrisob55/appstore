data/reviews.json:
	poetry run python3 -m appstore.get_reviews -o $@

requirements.txt: poetry.lock pyproject.toml
	poetry export -f requirements.txt --output requirements.txt
