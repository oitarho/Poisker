from __future__ import annotations

from app.core.config import settings


def listings_collection_schema() -> dict:
    """
    Typesense collection schema for listings.
    Postgres remains the source of truth; Typesense is for search + retrieval ordering.
    """

    return {
        "name": settings.typesense_listings_collection,
        "fields": [
            {"name": "id", "type": "string"},
            {"name": "title", "type": "string"},
            {"name": "description", "type": "string"},
            {"name": "kind", "type": "string", "facet": True},
            {"name": "status", "type": "string", "facet": True},
            {"name": "category_id", "type": "string", "facet": True},
            {"name": "location_id", "type": "string", "facet": True},
            {"name": "owner_id", "type": "string", "facet": True},
            {"name": "price", "type": "float"},
            {"name": "created_at", "type": "int64"},
            {"name": "published_at", "type": "int64", "optional": True},
            {"name": "views_count", "type": "int32"},
            {"name": "favorites_count", "type": "int32"},
            {"name": "boost_score", "type": "float"},
        ],
        "default_sorting_field": "boost_score",
    }
