"""Update the OpenAPI schema from the Belvo API.

Copyright (c) 2025 Edgar Ramírez-Mondragón
"""  # noqa: INP001

from __future__ import annotations

import json
import pathlib

import requests

OPENAPI_URL = "https://developers.belvo.com/_spec/apis/BelvoOpenApiSpec.json"
PATH = "tap_belvo/openapi.json"


def main() -> None:
    """Update the OpenAPI schema from the Belvo API."""
    with pathlib.Path(PATH).open("w", encoding="utf-8") as file:
        response = requests.get(OPENAPI_URL, timeout=5)
        response.raise_for_status()
        spec = response.json()

        content = json.dumps(spec, indent=2) + "\n"
        file.write(content)


if __name__ == "__main__":
    main()
