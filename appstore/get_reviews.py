import json
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
        "id": d["id"],
        "rating": d["attributes"]["rating"],
        "review": d["attributes"]["body"],
        "date": d["attributes"]["createdDate"][:10],
    }
    return out


@click.command()
@click.option(
    "-o",
    "--output-path",
    required=True,
    default="reviews.json",
    help="Output file",
)
def get_reviews(output_path):
    """Get all of the reviews available.
    :param output_path: Where to write the reviews, in json format.
    :type output_path: str
    :return: A list of dicts, each of which is the output of
        `parse_review_dict`.
    :rtype: list
    """
    _, output_ext = os.path.splitext(output_path)
    if not output_ext == ".json":
        raise ValueError("`output_path` must end with '.json'")
    private_key_path = os.environ["P8_KEY_PATH"]
    key_id = os.environ["KEY_ID"]
    app_id = os.environ["APP_ID"]
    limit = 200
    next_url = "".join(
        [
            "https://api.appstoreconnect.apple.com/v1/apps/",
            app_id,
            "/customerReviews?limit=",
            str(limit),
            "&sort=createdDate",
        ]
    )
    signed_key = sign_authlib(private_key_path, key_id, 1200)
    n_reviews = requests.get(
        next_url,
        headers={"Authorization": f"Bearer {signed_key}"},
    ).json()["meta"]["paging"]["total"]
    n_pages = (n_reviews // limit) + 1

    out = []
    has_more = True
    for i in tqdm(range(0, n_pages)):
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
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Written {n_reviews} reviews to {output_path}")
    return out


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    get_reviews()
