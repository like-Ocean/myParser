from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from core.database import get_db
from schemas.product import ProductResponse, ProductCreate, ProductUpdate
import service.product_service as product_service

router = APIRouter(prefix="/items", tags=["Items"])


@router.get("", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0, limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await product_service.get_products(db, skip, limit)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    return await product_service.get_product_by_id(db, product_id)


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    return await product_service.create_product(db, product)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    return await product_service.update_product(db, product_id, product_update)


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    await product_service.delete_product(db, product_id)


@router.delete("", status_code=200)
async def delete_all_products(db: AsyncSession = Depends(get_db)):
    deleted_count = await product_service.delete_all_products(db)
    return {
        "message": "All products deleted successfully",
        "deleted_count": deleted_count
    }
