from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.modules.categories.models import Category, CategoryScope


@dataclass(frozen=True, slots=True)
class SeedCat:
    name: str
    scope: CategoryScope = CategoryScope.both
    children: tuple["SeedCat", ...] = ()


def _slugify(name: str) -> str:
    return (
        name.strip()
        .lower()
        .replace("  ", " ")
        .replace("/", "-")
        .replace("—", "-")
        .replace("–", "-")
        .replace(" ", "-")
    )


SEED: tuple[SeedCat, ...] = (
    SeedCat(
        name="Transport",
        scope=CategoryScope.product,
        children=(SeedCat(name="Cars", scope=CategoryScope.product), SeedCat(name="Auto parts", scope=CategoryScope.product)),
    ),
    SeedCat(
        name="Electronics",
        scope=CategoryScope.product,
        children=(SeedCat(name="Phones", scope=CategoryScope.product), SeedCat(name="Computers", scope=CategoryScope.product)),
    ),
    SeedCat(name="Real Estate", scope=CategoryScope.product),
    SeedCat(name="Jobs", scope=CategoryScope.service),
    SeedCat(
        name="Services",
        scope=CategoryScope.service,
        children=(SeedCat(name="Repair", scope=CategoryScope.service), SeedCat(name="Delivery", scope=CategoryScope.service)),
    ),
    SeedCat(name="Home and Repair", scope=CategoryScope.both),
    SeedCat(name="Clothing", scope=CategoryScope.product),
    SeedCat(name="Kids", scope=CategoryScope.product),
    SeedCat(name="Agriculture", scope=CategoryScope.product),
    SeedCat(name="Other", scope=CategoryScope.both),
)


async def _upsert(*, session, name: str, scope: CategoryScope, parent: Category | None) -> Category:
    slug = _slugify(name) if parent is None else f"{parent.slug}/{_slugify(name)}"
    existing = await session.scalar(select(Category).where(Category.slug == slug))
    if existing:
        existing.name = name
        existing.scope = scope
        existing.parent_id = parent.id if parent else None
        return existing

    row = Category(name=name, slug=slug, scope=scope, parent_id=parent.id if parent else None)
    session.add(row)
    await session.flush()
    return row


async def seed_categories() -> None:
    async with AsyncSessionLocal() as session:
        for root in SEED:
            root_row = await _upsert(session=session, name=root.name, scope=root.scope, parent=None)
            for child in root.children:
                await _upsert(session=session, name=child.name, scope=child.scope, parent=root_row)
        await session.commit()


def main() -> None:
    print(f"Seeding categories into {settings.database_url}")
    asyncio.run(seed_categories())
    print("Done.")


if __name__ == "__main__":
    main()

