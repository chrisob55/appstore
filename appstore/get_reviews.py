import json
import logging
import os

import click
import requests
from dotenv import find_dotenv, load_dotenv
from tqdm import tqdm

from appstore.auth import sign_authlib


def parse_review_dict(d):
    """Get the useful info from the review data.
    :param d: The dictionary from the JSON response.
    :type d: dict
    :return: Dictionary with keys `"id"`, `"rating"`, `"review"`, `"date"`.
    :rtype: dict
    """
    out = {
        "review_id": d["id"],
        "rating": d["attributes"]["rating"],
        "review": d["attributes"]["body"],
        "date": d["attributes"]["createdDate"][:10],
    }
    return out


def get_reviews_version(version_id, signed_key):
    """Get all reviews for a particular version id of the app."""
    next_url = "".join(
        [
            "https://api.appstoreconnect.apple.com/v1/appStoreVersions/",
            version_id,
            "/customerReviews",
        ]
    )
    first_response = requests.get(
        next_url,
        headers={"Authorization": f"Bearer {signed_key}"},
    ).json()
    n_reviews = first_response["meta"]["paging"]["total"]
    limit = first_response["meta"]["paging"]["limit"]
    n_pages = (n_reviews // limit) + 1

    out = []
    has_more = True
    for i in range(0, n_pages):
        r = requests.get(
            next_url, headers={"Authorization": f"Bearer {signed_key}"}
        ).json()
        parsed_reviews = [parse_review_dict(d) for d in r["data"]]
        for review in parsed_reviews:
            out.append(review)
        next_url = r["links"].get("next", "")
        has_more = "next" in r["links"]
    if has_more:
        raise ValueError(
            "More reviews to collect, n_pages calculated incorrectly."
        )
    return out


@click.command()
@click.option(
    "-i",
    "--input-path",
    required=True,
    help="Path to the JSON file of app versions.",
)
@click.option(
    "-o",
    "--output-path",
    required=True,
    help="Path to write the outputs",
)
def get_reviews(input_path, output_path):
    """Get all of the reviews available.
    :param output_path: Where to write the reviews, in json format.
    :type output_path: str
    :return: A list of dicts, each of which is the output of
        `parse_review_dict`.
    :rtype: list
    """
    logger = logging.getLogger(__name__)
    _, input_ext = os.path.splitext(input_path)
    if not input_ext == ".json":
        raise ValueError("`input_path` must end with '.json'")
    _, output_ext = os.path.splitext(output_path)
    if not output_ext == ".json":
        raise ValueError("`output_path` must end with '.json'")
    private_key_path = os.environ["P8_KEY_PATH"]
    key_id = os.environ["KEY_ID"]
    with open(input_path, "r") as f:
        versions = json.load(f)
    version_ids = versions.keys()
    signed_key = sign_authlib(private_key_path, key_id, 1200)
    out = []
    for id in tqdm(version_ids):
        logger.info(f"Getting reviews for version {id}")
        try:
            out.append(
                {"version_id": id, "data": get_reviews_version(id, signed_key)}
            )
            logger.info(f"Collected reviews for version {id}")
        except ValueError:
            with open(f"data/{id}.txt", "w") as f:
                f.write(f"version id {id} failed")
            logger.warning(f"Failed to collect reviews for version {id}")

    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Written reviews for {len(out)} versions to {output_path}")
    return out


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    load_dotenv(find_dotenv())
    get_reviews()
