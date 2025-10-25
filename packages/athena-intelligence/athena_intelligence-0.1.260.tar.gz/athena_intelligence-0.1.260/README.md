# Athena Intelligence Python Library

[![fern shield](https://img.shields.io/badge/%F0%9F%8C%BF-SDK%20generated%20by%20Fern-brightgreen)](https://github.com/fern-api/fern)
[![pypi](https://img.shields.io/pypi/v/athena-intelligence.svg)](https://pypi.python.org/pypi/athena-intelligence)

The Athena Intelligence Python Library provides convenient access to the Athena Intelligence API from 
applications written in Python. 

The library includes type definitions for all 
request and response fields, and offers both synchronous and asynchronous clients powered by httpx.

## Installation

Add this dependency to your project's build file:

```bash
pip install athena-intelligence
# or
poetry add athena-intelligence
```

## Usage
Simply import `Athena` and start making calls to our API. 

```python
from athena.client import Athena
from athena import Model, Tools

client = Athena(
  api_key="YOUR_API_KEY" # Defaults to ATHENA_API_KEY
)
message = client.message.submit(
    content="visit www.athenaintelligence.ai and summarize the website in one paragraph",
    model=Model.GPT_3_5_TURBO,
    tools=[Tools.SEARCH, Tools.BROWSE, Tools.SEARCH],
)
```

## Async Client
The SDK also exports an async client so that you can make non-blocking
calls to our API. 

```python
from athena.client import AsyncAthena
from athena import Model, Tools

client = AsyncAthena(
  api_key="YOUR_API_KEY" # Defaults to ATHENA_API_KEY
)

async def main() -> None:
    message = client.message.submit(
      content="visit www.athenaintelligence.ai and summarize the website in one paragraph",
      model=Model.GPT_3_5_TURBO,
      tools=[Tools.SEARCH, Tools.BROWSE, Tools.SEARCH],
    )
    print("Received message", message)

asyncio.run(main())
```

## Polling
The SDK provides helper functions that will automatically poll when 
retrieving a message. Use the `submit_and_poll` method as shown below: 

```python
from athena.client import Athena
from athena import Model, Tools

client = Athena(api_key="...")
message =  client.message.submit_and_poll(
  content="visit www.athenaintelligence.ai and summarize the website in one paragraph",
  model=Model.GPT_3_5_TURBO,
  tools=[Tools.SEARCH, Tools.BROWSE, Tools.SEARCH],
)
```

By default, the method will poll every 2 seconds but you can override
this with the `poll_interval` argument.

## Athena Module
All of the models are nested within the Athena module. Let IntelliSense 
guide you! 

## Exception Handling
All errors thrown by the SDK will be subclasses of [`ApiError`](./src/athena/core/api_error.py).

```python
import athena

try:
  client.messages.get(...)
except athena.core.ApiError as e: # Handle all errors
  print(e.status_code)
  print(e.body)
```

## Advanced

### Timeouts
By default, requests time out after 60 seconds. You can configure this with a 
timeout option at the client or request level.

```python
from athena.client import Athena

client = Athena(
    # All timeouts are 20 seconds
    timeout=20.0,
)

# Override timeout for a specific method
client.messages.get(..., {
    timeout_in_seconds=20
})
```

### Custom HTTP client
You can override the httpx client to customize it for your use-case. Some common use-cases 
include support for proxies and transports.

```python
import httpx

from athena.client import Athena

client = Athena(
    http_client=httpx.Client(
        proxies="http://my.test.proxy.example.com",
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
    ),
)
```

## Beta Status

This SDK is in **Preview**, and there may be breaking changes between versions without a major 
version update. 

To ensure a reproducible environment (and minimize risk of breaking changes), we recommend pinning a specific package version.

## Contributing

While we value open-source contributions to this SDK, this library is generated programmatically. 
Additions made directly to this library would have to be moved over to our generation code, 
otherwise they would be overwritten upon the next generated release. Feel free to open a PR as
 a proof of concept, but know that we will not be able to merge it as-is. We suggest opening 
an issue first to discuss with us!

On the other hand, contributions to the README are always very welcome!
