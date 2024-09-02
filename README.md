# Downloading App Store Reviews

This project will download App Store Reviews.

For this to work you must set env vars `P8_KEY_PATH`, `KEY_ID`, and `APP_ID` in a file called `.env` at the top level of this directory. Both the P8 file and the `.env` file must **NEVER** be committed to version control.

When you check out the repo you will need to initialise the virtualenv. There are two ways to do this: using [poetry](https://python-poetry.org/) or using `requirements.txt`.

## Setup

### With Poetry

If you haven't already you will need to [install Poetry](https://python-poetry.org/docs/#installation) first. That will make it available to you system-wide.

Once that's done the `pyproject.toml` and `poetry.lock` files have all the info needed to create the environment. From within the project run:

```bash
poetry install
# Set up the pre-commit hooks
pre-commit install
```

That will initialise the virtual environment and install the required packages.

### With `requirements.txt`

In case you can't install Poetry, or just prefer not to use it, the required packages are specified in `requirements.txt`. Simply create a Python virtual environment, activate it, and then install from that file:

```bash
python3 -m virtualenv .venv
source ./.venv/bin/activate
pip install -r requirements.txt
# Set up the pre-commit hooks
pre-commit install
```

## Downloading the reviews

The `all` command is specified in the Makefile to write the reviews out at `data/reviews.json`. 

```bash
make all
```

If you'd prefer not to use the Makefile you can run:

```bash
# Using a poetry environment
# First get the app versions
poetry run python3 -m appstore.get_versions -o path/to/versions.json
# Then download the reviews for each app version
poetry run python3 -m appstore.get_reviews \
    -i path/to/versions.json \
    -o path/to/reviews.json
```

If you're using a non_poetry environment just remove the `poetry run` from the beginning of each command.
