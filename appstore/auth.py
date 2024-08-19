import datetime

from authlib.jose import jwt


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
