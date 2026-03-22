from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Category
from app.schemas.admin import CategoryResponse

router = APIRouter()


@router.get("/")
async def list_categories(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Category)
        .where(Category.is_active == True)
        .order_by(Category.sort_order.asc())
    )
    categories = result.scalars().all()

    return {
        "items": [CategoryResponse.model_validate(c) for c in categories]
    }
