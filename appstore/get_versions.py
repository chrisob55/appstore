import json
import logging
import os

import click
import requests
from dotenv import find_dotenv, load_dotenv

from appstore.auth import sign_authlib


@click.command()
@click.option(
    "-o",
    "--output-path",
    required=True,
    help="Output file",
)
def get_versions(output_path):
    """Get all versions of a given app.
    :param output_path: Where to write the reviews, in json format.
    :type output_path: str
    :return: A list of dicts, each of which is the output of
        `parse_review_dict`.
    :rtype: list
    """
    logger = logging.getLogger(__name__)
    _, output_ext = os.path.splitext(output_path)
    if not output_ext == ".json":
        raise ValueError("`output_path` must end with '.json'")
    private_key_path = os.environ["P8_KEY_PATH"]
    key_id = os.environ["KEY_ID"]
    app_id = os.environ["APP_ID"]
    logger.info(f"Getting version ids for App: {app_id}")

    next_url = "".join(
        [
            "https://api.appstoreconnect.apple.com/v1/apps/",
            app_id,
            "/appStoreVersions",
        ]
    )
    signed_key = sign_authlib(private_key_path, key_id, 1200)

    first_response = requests.get(
        next_url,
        headers={"Authorization": f"Bearer {signed_key}"},
    ).json()
    n_versions = first_response["meta"]["paging"]["total"]
    limit = first_response["meta"]["paging"]["limit"]
    n_pages = (n_versions // limit) + 1

    out = {}
    has_more = True
    for i in range(n_pages):
        r = requests.get(
            next_url,
            headers={"Authorization": f"Bearer {signed_key}"},
        ).json()
        out.update(
            {
                x["id"]: x["attributes"]["versionString"]
                for x in r["data"]
                if x["type"] == "appStoreVersions"
            }
        )
        next_url = r["links"].get("next", "")
        has_more = "next" in r["links"]
    if has_more:
        raise ValueError(
            "More versions to collect, n_pages calculated incorrectly."
        )
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    logger.info(f"Written {len(out)} versions to {output_path}")
    return out


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    load_dotenv(find_dotenv())
    get_versions()
