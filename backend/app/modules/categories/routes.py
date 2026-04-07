from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.api.deps import DbSession
from app.core.errors import NotFoundError
from app.modules.categories.models import Category, CategoryScope
from app.modules.categories.schemas import CategoryListResponse, CategoryOut
from app.modules.listings.models import ListingKind

router = APIRouter(prefix="/categories", tags=["categories"])


def _out(c: Category) -> CategoryOut:
    return CategoryOut(
        id=c.id,
        name=c.name,
        slug=c.slug,
        scope=c.scope,
        parent_id=c.parent_id,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _scope_filter(kind: ListingKind | None):
    if kind is None:
        return None
    if kind == ListingKind.product:
        return or_(Category.scope == CategoryScope.product, Category.scope == CategoryScope.both)
    return or_(Category.scope == CategoryScope.service, Category.scope == CategoryScope.both)


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    db: DbSession,
    kind: ListingKind | None = Query(default=None, description="Optional kind filter: product/service"),
) -> CategoryListResponse:
    stmt = select(Category).where(Category.parent_id.is_(None)).order_by(Category.name)
    f = _scope_filter(kind)
    if f is not None:
        stmt = stmt.where(f)
    rows = (await db.scalars(stmt)).all()
    return CategoryListResponse(items=[_out(x) for x in rows])


@router.get("/{parent_id}/children", response_model=CategoryListResponse)
async def list_child_categories(
    parent_id: UUID,
    db: DbSession,
    kind: ListingKind | None = Query(default=None, description="Optional kind filter: product/service"),
) -> CategoryListResponse:
    stmt = select(Category).where(Category.parent_id == parent_id).order_by(Category.name)
    f = _scope_filter(kind)
    if f is not None:
        stmt = stmt.where(f)
    rows = (await db.scalars(stmt)).all()
    return CategoryListResponse(items=[_out(x) for x in rows])


@router.get("/{category_id}", response_model=CategoryOut)
async def get_category(category_id: UUID, db: DbSession) -> CategoryOut:
    row = await db.get(Category, category_id)
    if row is None:
        raise NotFoundError("Category not found")
    return _out(row)

