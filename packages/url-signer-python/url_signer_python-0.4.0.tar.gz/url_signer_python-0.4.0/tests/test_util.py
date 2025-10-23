import os
from ioriver.url_signer import UrlSigner

def get_signer():
    private_key = None
    encryption_key = "abcdef1234"
    with open(os.path.join(os.path.dirname(__file__), 'private_key.pem'), 'r') as key_file:
        private_key = key_file.read()
    assert private_key is not None

    providers_key_info = {
        "cloudfront_key_id": "1234",
        "fastly_key_id": "5678",
        "akamai_key_id": "token-123"
    }

    signer = UrlSigner(private_key, encryption_key, providers_key_info)
    return signer
