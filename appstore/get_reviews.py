import os
import datetime
import click
from authlib.jose import jwt
import requests
import json
from tqdm import tqdm
from dotenv import load_dotenv, find_dotenv


def sign_authlib(private_key_path, key_id, valid_for):
    """Generates the authentication key required for the App Store
    Connect API.
    :param private_key_path: Path to the P8 private key from the App
        Store.
    :type private_key_path: str
    :param key_id: Key ID from the P8 file. By default this will be in
        the filename itself.
    :type key_id: str
    :return: The signed key to authenticate.
    :rtype: str

    """
    current_time = int(datetime.datetime.now().timestamp())
    header = {"alg": "ES256", "kid": key_id, "typ": "JWT"}

    payload = {
        "iss": "69a6de77-4258-47e3-e053-5b8c7c11a4d1",
        "iat": current_time,
        "exp": current_time + valid_for,
        "aud": "appstoreconnect-v1",
    }
    with open(private_key_path, "rb") as fh:
        signing_key = fh.read()
    token = jwt.encode(header, payload, key=signing_key)
    decoded = token.decode()
    return decoded


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
@click.option("-k", "--key-id", required=True, help="Key ID")
@click.option("-a", "--app-id", required=True, help="App ID")
@click.option(
    "-o",
    "--output-path",
    required=True,
    default="reviews.json",
    help="Output file",
)
def get_reviews(key_id, app_id, output_path):
    """Get all of the reviews available.
    :param key_id: Key ID from the P8 file. By default this will be in
        the filename itself.
    :type key_id: str
    :param app_id: The id number for the app in the App Store.
    :type app_id: str
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
