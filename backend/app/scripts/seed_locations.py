from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.modules.locations.models import Location, LocationType


@dataclass(frozen=True, slots=True)
class SeedLoc:
    name: str
    type: LocationType
    children: tuple["SeedLoc", ...] = ()


def _slugify(name: str) -> str:
    # Keep it simple and stable for MVP; supports Cyrillic.
    return (
        name.strip()
        .lower()
        .replace("  ", " ")
        .replace("/", "-")
        .replace("—", "-")
        .replace("–", "-")
        .replace(" ", "-")
    )


SEED: tuple[SeedLoc, ...] = (
    SeedLoc(
        name="Чеченская Республика",
        type=LocationType.republic,
        children=(
            SeedLoc(
                name="Грозненский район",
                type=LocationType.district,
                children=(
                    SeedLoc(name="Грозный", type=LocationType.city),
                    SeedLoc(name="Аргун", type=LocationType.city),
                ),
            ),
            SeedLoc(
                name="Гудермесский район",
                type=LocationType.district,
                children=(
                    SeedLoc(name="Гудермес", type=LocationType.city),
                    SeedLoc(name="Джалка", type=LocationType.village),
                ),
            ),
            SeedLoc(
                name="Урус-Мартановский район",
                type=LocationType.district,
                children=(
                    SeedLoc(name="Урус-Мартан", type=LocationType.city),
                    SeedLoc(name="Алхан-Юрт", type=LocationType.village),
                ),
            ),
            SeedLoc(
                name="Шалинский район",
                type=LocationType.district,
                children=(
                    SeedLoc(name="Шали", type=LocationType.city),
                    SeedLoc(name="Герменчук", type=LocationType.village),
                ),
            ),
        ),
    ),
)


async def _upsert_location(*, session, name: str, type_: LocationType, parent: Location | None) -> Location:
    slug = _slugify(name) if parent is None else f"{parent.slug}/{_slugify(name)}"
    existing = await session.scalar(select(Location).where(Location.slug == slug))
    if existing:
        existing.name = name
        existing.type = type_
        existing.parent_id = parent.id if parent else None
        return existing

    loc = Location(
        name=name,
        slug=slug,
        type=type_,
        parent_id=parent.id if parent else None,
        latitude=None,
        longitude=None,
    )
    session.add(loc)
    await session.flush()
    return loc


async def seed_locations() -> None:
    async with AsyncSessionLocal() as session:
        for root in SEED:
            root_row = await _upsert_location(session=session, name=root.name, type_=root.type, parent=None)
            for district in root.children:
                district_row = await _upsert_location(
                    session=session, name=district.name, type_=district.type, parent=root_row
                )
                for child in district.children:
                    await _upsert_location(
                        session=session, name=child.name, type_=child.type, parent=district_row
                    )

        await session.commit()


def main() -> None:
    # Uses POISKER_DATABASE_URL from env/.env
    print(f"Seeding locations into {settings.database_url}")
    asyncio.run(seed_locations())
    print("Done.")


if __name__ == "__main__":
    main()

