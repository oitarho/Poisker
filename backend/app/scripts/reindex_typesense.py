from __future__ import annotations

import asyncio

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.modules.search.indexer import reindex_all_active


async def run() -> None:
    async with AsyncSessionLocal() as session:
        count = await reindex_all_active(session)
        await session.commit()
        print(f"Reindexed {count} active listings into Typesense collection '{settings.typesense_listings_collection}'.")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

