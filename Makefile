data/reviews.json:
	poetry run \
	python -m appstore.get_reviews \
	-k 9HSHRGCVJK \
	-a 514561561 \
	-o $@

requirements.txt: poetry.lock pyproject.toml
	poetry export -f requirements.txt --output requirements.txt
