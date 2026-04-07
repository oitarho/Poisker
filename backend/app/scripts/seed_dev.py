from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.modules.categories.models import Category
from app.modules.chats.models import Conversation, ConversationParticipant, Message
from app.modules.favorites.models import Favorite
from app.modules.listings.models import Listing, ListingKind, ListingPhoto, ListingStatus
from app.modules.locations.models import Location
from app.modules.reviews.service import create_review, recompute_user_rating
from app.modules.search.indexer import reindex_all_active
from app.modules.users.models import RefreshToken, User
from app.core.security import hash_password
from app.modules.moderation.models import ModerationLog


def _now() -> datetime:
    return datetime.now(timezone.utc)


DEMO_DOMAIN = "poisker.local"
DEMO_PASSWORD = "Password123!"


@dataclass(frozen=True, slots=True)
class DemoUserSeed:
    email: str
    full_name: str
    phone: str | None


USERS: list[DemoUserSeed] = [
    DemoUserSeed(email=f"demo{i:02d}@{DEMO_DOMAIN}", full_name=name, phone=None)
    for i, name in enumerate(
        [
            "Adam A.",
            "Amina B.",
            "Isa C.",
            "Fatima D.",
            "Umar E.",
            "Zara F.",
            "Khadijat G.",
            "Musa H.",
            "Maryam I.",
            "Yusuf J.",
            "Aisha K.",
            "Ali L.",
            "Hava M.",
            "Said N.",
            "Madina O.",
            "Islam P.",
        ],
        start=1,
    )
]


PRODUCT_TITLES = [
    "iPhone 13 128GB",
    "Samsung Galaxy S22",
    "Laptop Lenovo IdeaPad",
    "Toyota Corolla parts",
    "Baby stroller",
    "Winter jacket",
    "Mountain bike",
    "Washing machine",
    "Gaming console",
    "Electric kettle",
]

SERVICE_TITLES = [
    "Phone screen replacement",
    "Home cleaning service",
    "Courier delivery around Grozny",
    "Plumbing repair",
    "Car diagnostics",
    "Tutoring (math)",
    "Website setup",
    "Air conditioner installation",
    "Moving assistance",
    "Haircut at home",
]


async def _cleanup_demo(session) -> None:
    # delete by demo email set (idempotent)
    demo_users = (await session.scalars(select(User).where(User.email.like(f"demo%@{DEMO_DOMAIN}")))).all()
    if not demo_users:
        return
    demo_ids = [u.id for u in demo_users]

    # conversations where either party is demo user
    demo_convs = (
        await session.scalars(
            select(Conversation).where(
                (Conversation.owner_user_id.in_(demo_ids))
                | (Conversation.interested_user_id.in_(demo_ids))
            )
        )
    ).all()
    conv_ids = [c.id for c in demo_convs]

    if conv_ids:
        await session.execute(delete(Message).where(Message.conversation_id.in_(conv_ids)))
        await session.execute(delete(ConversationParticipant).where(ConversationParticipant.conversation_id.in_(conv_ids)))
        await session.execute(delete(Conversation).where(Conversation.id.in_(conv_ids)))

    # favorites by demo users
    await session.execute(delete(Favorite).where(Favorite.user_id.in_(demo_ids)))

    # reviews by or for demo users
    from app.modules.reviews.models import Review

    await session.execute(
        delete(Review).where((Review.reviewer_id.in_(demo_ids)) | (Review.target_user_id.in_(demo_ids)))
    )

    # listings owned by demo users + related photos/favorites
    demo_listings = (await session.scalars(select(Listing).where(Listing.owner_id.in_(demo_ids)))).all()
    listing_ids = [l.id for l in demo_listings]
    if listing_ids:
        await session.execute(delete(ListingPhoto).where(ListingPhoto.listing_id.in_(listing_ids)))
        await session.execute(delete(Favorite).where(Favorite.listing_id.in_(listing_ids)))
        await session.execute(delete(ModerationLog).where(ModerationLog.listing_id.in_(listing_ids)))
        await session.execute(delete(Listing).where(Listing.id.in_(listing_ids)))

    await session.execute(delete(RefreshToken).where(RefreshToken.user_id.in_(demo_ids)))
    await session.execute(delete(User).where(User.id.in_(demo_ids)))


async def seed_dev() -> None:
    random.seed(42)
    async with AsyncSessionLocal() as session:
        # Ensure base seeds exist (locations/categories) via separate make targets.
        await _cleanup_demo(session)
        await session.commit()

        # Fetch some locations/categories for assigning.
        locations = (await session.scalars(select(Location).order_by(Location.name))).all()
        categories = (await session.scalars(select(Category).order_by(Category.name))).all()
        if not locations or not categories:
            raise RuntimeError("Seed locations and categories first.")

        # Create users
        users: list[User] = []
        for u in USERS:
            row = User(
                email=u.email,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name=u.full_name,
                phone_number=u.phone,
                is_email_verified=True,
                is_phone_verified=False,
            )
            session.add(row)
            users.append(row)
        await session.flush()

        # Create listings
        listings: list[Listing] = []
        now = _now()
        for i in range(40):
            kind = ListingKind.product if i < 22 else ListingKind.service
            title = random.choice(PRODUCT_TITLES if kind == ListingKind.product else SERVICE_TITLES)
            owner = random.choice(users)
            loc = random.choice(locations)
            cat = random.choice(categories)
            status = ListingStatus.active if i % 3 != 0 else ListingStatus.pending
            created_at = now - timedelta(days=random.randint(0, 20), hours=random.randint(0, 23))
            published_at = created_at if status == ListingStatus.active else None
            price = float(random.randint(500, 120000)) if kind == ListingKind.product else float(random.randint(500, 15000))

            l = Listing(
                owner_id=owner.id,
                kind=kind,
                status=status,
                title=title,
                description=f"{title}. Safe demo data for Poisker development.",
                price=price,
                location_id=loc.id,
                category_id=cat.id,
                published_at=published_at,
                views_count=random.randint(0, 800),
                favorites_count=0,
                boost_score=0,
            )
            # override timestamps for realism
            l.created_at = created_at
            l.updated_at = created_at
            session.add(l)
            listings.append(l)
        await session.flush()

        # Add photo metadata placeholders (no real files)
        for l in listings:
            n = 0 if random.random() < 0.25 else random.randint(1, 4)
            for idx in range(n):
                session.add(
                    ListingPhoto(
                        listing_id=l.id,
                        key=f"seed/listings/{l.id}/{idx}.jpg",
                        content_type="image/jpeg",
                        sort_order=idx,
                    )
                )
        await session.flush()

        # Favorites (only for active listings)
        active_listings = [l for l in listings if l.status == ListingStatus.active]
        for _ in range(120):
            u = random.choice(users)
            l = random.choice(active_listings)
            if l.owner_id == u.id:
                continue
            session.add(Favorite(user_id=u.id, listing_id=l.id))
        await session.flush()

        # Recompute favorites_count
        fav_counts = (
            await session.execute(
                select(Favorite.listing_id, func.count(Favorite.id)).group_by(Favorite.listing_id)
            )
        ).all()
        by_lid = {lid: int(c) for (lid, c) in fav_counts}
        for l in listings:
            l.favorites_count = by_lid.get(l.id, 0)

        # Conversations + messages
        convs: list[Conversation] = []
        for l in random.sample(active_listings, k=min(12, len(active_listings))):
            interested = random.choice([u for u in users if u.id != l.owner_id])
            conv = Conversation(listing_id=l.id, owner_user_id=l.owner_id, interested_user_id=interested.id)
            session.add(conv)
            convs.append(conv)
        await session.flush()
        for c in convs:
            session.add_all(
                [
                    ConversationParticipant(conversation_id=c.id, user_id=c.owner_user_id, last_read_at=None),
                    ConversationParticipant(conversation_id=c.id, user_id=c.interested_user_id, last_read_at=None),
                ]
            )
        await session.flush()

        sample_msgs = [
            "Здравствуйте! Актуально?",
            "Да, актуально.",
            "Можно торг?",
            "Немного.",
            "Когда можно посмотреть?",
            "Сегодня вечером удобно.",
        ]
        for c in convs:
            for i in range(random.randint(2, 8)):
                sender = c.interested_user_id if i % 2 == 0 else c.owner_user_id
                session.add(Message(conversation_id=c.id, sender_id=sender, body=random.choice(sample_msgs)))
        await session.flush()

        # Reviews (listing-linked, target is listing owner)
        for l in random.sample(active_listings, k=min(15, len(active_listings))):
            reviewer = random.choice([u for u in users if u.id != l.owner_id])
            await create_review(
                session,
                reviewer_id=reviewer.id,
                target_user_id=l.owner_id,
                listing_id=l.id,
                rating=random.randint(3, 5),
                text="Demo review: everything was fine.",
            )
        # recompute for all demo users (covers any duplicates skipped)
        for u in users:
            await recompute_user_rating(session, user_id=u.id)

        await session.commit()

        # Typesense reindex (active only)
        await reindex_all_active(session)
        await session.commit()


def main() -> None:
    print(f"Dev seeding into {settings.database_url}")
    asyncio.run(seed_dev())
    print("Done. Demo password for all demo users:", DEMO_PASSWORD)


if __name__ == "__main__":
    main()

