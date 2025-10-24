"""
Parze Python SDK
A simple client for interacting with the Parze API.
"""

import requests

class ParzeClient:
    def __init__(self, api_key: str, base_url: str = "https://api.parze.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def extract(self, document: str, schema: dict) -> dict:
        """
        Extract data from a document using a schema.
        """
        url = f"{self.base_url}/api/extract"
        payload = {"document": document, "schema": schema}
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def parse(self, document: str) -> dict:
        """
        Parse a document and return structured data.
        """
        url = f"{self.base_url}/api/parse"
        payload = {"document": document}
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
