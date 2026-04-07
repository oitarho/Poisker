from __future__ import annotations

from functools import lru_cache

import typesense

from app.core.config import settings


@lru_cache(maxsize=1)
def get_typesense_client() -> typesense.Client:
    return typesense.Client(
        {
            "nodes": [
                {
                    "host": settings.typesense_host,
                    "port": settings.typesense_port,
                    "protocol": settings.typesense_protocol,
                }
            ],
            "api_key": settings.typesense_api_key,
            "connection_timeout_seconds": 2,
        }
    )
