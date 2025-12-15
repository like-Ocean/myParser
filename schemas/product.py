from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class ProductBase(BaseModel):
    name: str
    price: float
    old_price: Optional[float] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    availability: str = "available"


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    old_price: Optional[float] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    availability: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
