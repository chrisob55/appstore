import datetime
import click
from authlib.jose import jwt
import requests
import json
from tqdm import tqdm


def sign_authlib(private_key_path, key_id, valid_for):
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
    out = {
        "id": d["id"],
        "rating": d["attributes"]["rating"],
        "review": d["attributes"]["body"],
        "date": d["attributes"]["createdDate"][:10],
    }
    return out


@click.command()
@click.option(
    "-p", "--private-key-path", required=True, help="Path to the private p8 key"
)
@click.option("-k", "--key-id", required=True, help="Key ID")
@click.option("-a", "--app-id", required=True, help="App ID")
@click.option(
    "-n",
    "--n-pages",
    required=True,
    default=-1,
    help="Number of pages of reviews to fetch",
)
@click.option(
    "-o", "--output-path", required=True, default="reviews.json", help="Output file"
)
def get_reviews(private_key_path, key_id, app_id, n_pages, output_path):
    url = "".join(
        [
            "https://api.appstoreconnect.apple.com/v1/apps/",
            app_id,
            "/customerReviews?limit=200&sort=createdDate",
        ]
    )
    if n_pages < 0:
        signed_key = sign_authlib(private_key_path, key_id, 1200)
        n_pages = requests.get(
            url,
            headers={"Authorization": f"Bearer {signed_key}"},
        ).json()["meta"]["paging"]["total"]

    next_url = url
    out = []

    for i in tqdm(range(0, n_pages)):
        # Only generate a new key every 100 requests
        if i % 100 == 0:
            signed_key = sign_authlib(private_key_path, key_id, 1200)
        r = requests.get(
            next_url, headers={"Authorization": f"Bearer {signed_key}"}
        ).json()
        parsed_reviews = [parse_review_dict(d) for d in r["data"]]
        for review in parsed_reviews:
            out.append(review)
        next_url = r["links"]["next"]
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    n_reviews = len(out)
    print(f"Written {n_reviews} reviews to {output_path}")
    return n_reviews


if __name__ == "__main__":
    get_reviews()
