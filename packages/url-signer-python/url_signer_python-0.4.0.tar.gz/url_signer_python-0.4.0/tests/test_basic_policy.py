# pylint: disable=line-too-long,duplicate-code
import os
from ioriver.url_signer import UrlSigner


def test_basic_policy_signature():
    expected_signature = "Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly93d3cuZXhhbXBsZS5jb20vKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MzMxMzUyNjQwMH19fV19&Signature=wIFQbHL799IFPGSsf-etyXdOyAbl51sWE7Ab41petBrGJoj63vwKSuYp-vJUx9bjp3nRGgz-OkHDctp4pWgm4kW~ZaO6fZlnQWKnGuIWO4~ZTqXAbMbqnYHzvaiZSGZj0Ub6WER8jLC5sh7pl~7OXPMiBPots0EZM-8d8uyhQ4BNThUqOI5-fnE1~hxFPGvtqfNGu8xedygCZfrQZM6lEuf3B78Pex~9boBRxZ-vB~FYlp6tbGedpozPT0rgHOoOT6xpTzo0eJJPvjgBKoB5Hn5XZif4H6bwtZhtzW84MVjKgtjs-nFko8nUR5wsn~0iFt4K5YvMBY2iGnffEH8~qg__&Key-Pair-Id=1234&FS-Policy=cmVzb3VyY2VzPWh0dHBzJTNBJTJGJTJGd3d3LmV4YW1wbGUuY29tJTJGJTJBJmVuZF90aW1lPTMzMTM1MjY0MDA=&FS-Signature=Lh9LYj83zoX0fNH48eBmgciFsAQ7mDIZgDUfxgxfpPu8ZxDaocENvMMeHHMCEGjtzBnwm2+ESwHdW+4musaAcHKnqkylk7eGA2mPG1x9j9+pGMNg9ZpMaYl+dlZf3o2kjDCXdBgQsmPKvDYni4vT1PWH/5DRREqOTNQ5QVUIKzy6X+nXLzUlte75iqnlXyeZ3WPr/PWmIe3lQs/kKRIkMOjGOYJfFu3nKpdue0KRqOISr55ioaqi+B7+YGND05ko1frs1yq4eHECULZkbTaYpI9EqfGxbqlGL4V9FDZw/J23lO7tNjiaggO+yECo+Ozv8e/vRZ2s4D4KelNll5uOdA==&FS-Key-Id=5678"
    private_key = None
    encryption_key = "abcdef1234"
    with open(os.path.join(os.path.dirname(__file__), 'private_key.pem'), 'r') as key_file:
        private_key = key_file.read()
    assert private_key is not None

    providers_key_info = {
        "cloudfront_key_id": "1234",
        "fastly_key_id": "5678",
    }

    policy = {
        "resources": "https://www.example.com/*",
        "condition": {
            "end_time": 3313526400
        }
    }

    signer = UrlSigner(private_key, encryption_key, providers_key_info)
    assert signer.generate_url_signature(policy) == expected_signature
