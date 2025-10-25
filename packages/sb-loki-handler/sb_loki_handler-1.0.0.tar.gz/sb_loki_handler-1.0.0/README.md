# sb-loki-handler

Typed loki handler for logging

## Installation

You can install the package via pip:

```
pip install sb-loki-handler
```

## Usage

```python
import logging

from sb_loki_handler import LokiHandler

logger = logging.getLogger("my-logger")
logger.setLevel(logging.INFO)

handler = LokiHandler(
    "https://user:pass@host/loki/api/v1/push",
    labels={"application": "my-app"}
)
logger.addHandler(handler)


logger.info("Hello world.")
logger.info("With extra", extra={"labels": {"foo": "bar"}})

with handler.labels({"foo": "bar"}):
    logger.info("With context")

```

## License

This project is licensed under the terms of the MIT license.
