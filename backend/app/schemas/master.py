from datetime import datetime
from uuid import UUID
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    city: Optional[str] = None


class CategoryBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    master_id: UUID
    name: str
    description: Optional[str] = None
    price: float
    duration_minutes: int
    is_active: bool
    created_at: datetime


class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    duration_minutes: int = Field(..., gt=0)


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class PortfolioImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    image_url: str
    sort_order: int


class MasterProfileCreate(BaseModel):
    description: Optional[str] = None
    category_id: UUID
    district: Optional[str] = None
    work_hours: Optional[dict[str, Any]] = None


class MasterProfileUpdate(BaseModel):
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    district: Optional[str] = None
    work_hours: Optional[dict[str, Any]] = None
    is_available: Optional[bool] = None


class MasterListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user: UserBrief
    category: CategoryBrief
    description: Optional[str] = None
    district: Optional[str] = None
    rating_avg: float
    rating_count: int
    verification_status: str
    is_available: bool
    price_from: Optional[float] = None
    services_count: int


class MasterDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user: UserBrief
    category: CategoryBrief
    description: Optional[str] = None
    district: Optional[str] = None
    rating_avg: float
    rating_count: int
    verification_status: str
    is_available: bool
    price_from: Optional[float] = None
    services_count: int
    work_hours: Optional[dict[str, Any]] = None
    services: list[ServiceResponse] = []
    portfolio: list[PortfolioImageResponse] = []
    reviews_preview: list[Any] = []


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
