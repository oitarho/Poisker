from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from app.modules.listings.models import Listing
from app.modules.users.models import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


@dataclass(frozen=True, slots=True)
class RankingWeights:
    w_text: float = 0.50
    w_freshness: float = 0.20
    w_local: float = 0.00  # placeholder
    w_trust: float = 0.10
    w_photos: float = 0.10
    w_engagement: float = 0.10
    w_spam_penalty: float = 0.00  # placeholder (subtracted)


class RankingStrategy(Protocol):
    name: str

    def score(
        self,
        *,
        listing: Listing,
        owner: User,
        text_relevance: float,
        now: datetime,
    ) -> tuple[float, dict[str, float]]:
        """
        Returns (final_score, breakdown).

        text_relevance is expected to be normalized in [0..1] for the current query/page.
        """


def _freshness_score(listing: Listing, *, now: datetime, half_life_hours: float = 72.0) -> float:
    # Simple explainable decay: 1.0 at publish, then halves every half_life.
    ts = listing.published_at or listing.created_at
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age_hours = max(0.0, (now - ts).total_seconds() / 3600.0)
    # 2^(-age/half_life)
    return float(2 ** (-age_hours / max(1.0, half_life_hours)))


def _trust_score(owner: User) -> float:
    # Simple trust: verified signals + rating (bounded).
    verified = (1.0 if owner.is_email_verified else 0.0) * 0.4 + (1.0 if owner.is_phone_verified else 0.0) * 0.6
    rating = _clamp01(float(owner.rating) / 5.0)
    # Slightly favor verified accounts even with few reviews.
    return _clamp01(0.6 * rating + 0.4 * verified)


def _photos_score(listing: Listing) -> float:
    # 0 if none, 1 if 3+ photos, linear in between.
    n = len(listing.photos or [])
    return _clamp01(n / 3.0)


def _engagement_score(listing: Listing) -> float:
    # Cheap, explainable engagement: log-ish compression without importing math heavy logic.
    fav = float(listing.favorites_count or 0)
    views = float(listing.views_count or 0)
    # normalize with simple saturating curves
    fav_s = _clamp01(fav / 20.0)
    views_s = _clamp01(views / 500.0)
    return _clamp01(0.7 * fav_s + 0.3 * views_s)


@dataclass(frozen=True, slots=True)
class ProductRankingStrategy:
    name: str = "product"
    weights: RankingWeights = RankingWeights(
        w_text=0.55,
        w_freshness=0.20,
        w_local=0.00,  # placeholder
        w_trust=0.05,
        w_photos=0.10,
        w_engagement=0.10,
        w_spam_penalty=0.00,
    )

    def score(
        self,
        *,
        listing: Listing,
        owner: User,
        text_relevance: float,
        now: datetime,
    ) -> tuple[float, dict[str, float]]:
        freshness = _freshness_score(listing, now=now, half_life_hours=72.0)
        local_rel = 0.0  # placeholder
        trust = _trust_score(owner)
        photos = _photos_score(listing)
        engagement = _engagement_score(listing)
        spam_penalty = 0.0  # placeholder

        w = self.weights
        final = (
            w.w_text * _clamp01(text_relevance)
            + w.w_freshness * freshness
            + w.w_local * local_rel
            + w.w_trust * trust
            + w.w_photos * photos
            + w.w_engagement * engagement
            - w.w_spam_penalty * spam_penalty
        )
        breakdown = {
            "text": _clamp01(text_relevance),
            "freshness": freshness,
            "local": local_rel,
            "trust": trust,
            "photos": photos,
            "engagement": engagement,
            "spam_penalty": spam_penalty,
            "final": float(final),
        }
        return float(final), breakdown


@dataclass(frozen=True, slots=True)
class ServiceRankingStrategy:
    name: str = "service"
    weights: RankingWeights = RankingWeights(
        w_text=0.45,
        w_freshness=0.15,
        w_local=0.00,  # placeholder
        w_trust=0.30,  # provider reputation matters more
        w_photos=0.05,
        w_engagement=0.05,
        w_spam_penalty=0.00,
    )

    def score(
        self,
        *,
        listing: Listing,
        owner: User,
        text_relevance: float,
        now: datetime,
    ) -> tuple[float, dict[str, float]]:
        freshness = _freshness_score(listing, now=now, half_life_hours=120.0)
        local_rel = 0.0  # placeholder
        reputation = _trust_score(owner)
        profile_complete = 0.0  # placeholder
        response_quality = 0.0  # placeholder
        spam_penalty = 0.0  # placeholder

        photos = _photos_score(listing)
        engagement = _engagement_score(listing)

        w = self.weights
        final = (
            w.w_text * _clamp01(text_relevance)
            + w.w_freshness * freshness
            + w.w_local * local_rel
            + w.w_trust * reputation
            + w.w_photos * photos
            + w.w_engagement * engagement
            # placeholders get weights later (kept out of formula for now)
            - w.w_spam_penalty * spam_penalty
        )
        breakdown = {
            "text": _clamp01(text_relevance),
            "freshness": freshness,
            "local": local_rel,
            "provider_reputation": reputation,
            "profile_completeness": profile_complete,
            "response_quality": response_quality,
            "photos": photos,
            "engagement": engagement,
            "spam_penalty": spam_penalty,
            "final": float(final),
        }
        return float(final), breakdown

