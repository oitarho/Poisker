from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.models import Listing, ListingKind
from app.modules.ranking.strategies import (
    ProductRankingStrategy,
    RankingStrategy,
    ServiceRankingStrategy,
)
from app.modules.users.models import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class RankedItem:
    score: float
    breakdown: dict[str, float]


def get_strategy(kind: ListingKind) -> RankingStrategy:
    if kind == ListingKind.service:
        return ServiceRankingStrategy()
    return ProductRankingStrategy()


def score_listing(
    *,
    listing: Listing,
    owner: User,
    text_relevance: float,
    now: datetime | None = None,
) -> RankedItem:
    strategy = get_strategy(listing.kind)
    ts = now or _utcnow()
    score, breakdown = strategy.score(listing=listing, owner=owner, text_relevance=text_relevance, now=ts)
    return RankedItem(score=score, breakdown=breakdown)


def base_boost_score(
    *,
    listing: Listing,
    owner: User,
    now: datetime | None = None,
) -> RankedItem:
    """
    Query-independent score used as `Listing.boost_score`.

    We set text_relevance=0 so the base boost doesn't depend on a specific query.
    """
    return score_listing(listing=listing, owner=owner, text_relevance=0.0, now=now)

