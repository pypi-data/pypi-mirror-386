# Parze Python SDK

A simple client for interacting with the Parze API.

## Installation
```bash
pip install parze
```

## Usage
```python
from parze import ParzeClient

client = ParzeClient(api_key="YOUR_API_KEY")
result = client.extract(document="...", schema={...})
```
