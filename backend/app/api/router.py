from __future__ import annotations

from fastapi import APIRouter

from app.api.health import router as health_router
from app.modules.auth.routes import router as auth_router
from app.modules.categories.routes import router as categories_router
from app.modules.favorites.routes import router as favorites_router
from app.modules.chats.routes import router as chats_router
from app.modules.listings.routes import router as listings_router
from app.modules.locations.routes import router as locations_router
from app.modules.reviews.routes import router as reviews_router
from app.modules.search.routes import router as search_router
from app.modules.moderation.routes import router as moderation_admin_router
from app.modules.users.routes import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(locations_router)
api_router.include_router(categories_router)
api_router.include_router(listings_router)
api_router.include_router(favorites_router)
api_router.include_router(chats_router)
api_router.include_router(reviews_router)
api_router.include_router(search_router)
api_router.include_router(moderation_admin_router)
