# py_get_sequence_api_client

A Python client for the Sequence financial orchestration platform API.

## Features
- Async API access to Sequence accounts
- Pod, Income Source, Liability, Investment, and External account helpers
- Designed for integration with Home Assistant and other Python apps

## Installation
```bash
pip install py_get_sequence_api_client
```

## Usage
```python
import aiohttp
from py_get_sequence_api_client.client import SequenceApiClient

async def main():
    async with aiohttp.ClientSession() as session:
        client = SequenceApiClient(session, "YOUR_ACCESS_TOKEN")
        accounts = await client.async_get_accounts()
        print(accounts)
```

## Author
Dyllan Macias (@DellanX)

## License
See LICENSE file.
