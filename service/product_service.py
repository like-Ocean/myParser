from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
from fastapi import HTTPException
from models.product import Product
from schemas.product import ProductCreate, ProductUpdate
from service.nats_client import nats_client
from service.websocket_manager import manager


async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Product]:
    result = await db.execute(
        select(Product).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def get_product_by_id(db: AsyncSession, product_id: int) -> Product:
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


async def create_product(db: AsyncSession, product_data: ProductCreate) -> Product:
    new_product = Product(**product_data.model_dump())

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    await _notify_product_created(new_product)

    return new_product


async def update_product(db: AsyncSession,product_id: int,product_data: ProductUpdate) -> Product:
    product = await get_product_by_id(db, product_id)

    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    await _notify_product_updated(product)

    return product


async def delete_product(db: AsyncSession,product_id: int):
    product = await get_product_by_id(db, product_id)

    await db.delete(product)
    await db.commit()

    await _notify_product_deleted(product_id)


async def delete_all_products(db: AsyncSession) -> int:
    count_result = await db.execute(select(Product))
    products_count = len(count_result.scalars().all())

    if products_count == 0:
        return 0

    await db.execute(delete(Product))
    await db.commit()

    await _notify_all_products_deleted(products_count)

    return products_count


async def _notify_product_created(product: Product):
    message = {
        "action": "created",
        "product_id": product.id,
        "product_name": product.name,
        "price": product.price
    }

    await nats_client.publish("items.updates", message)

    await manager.broadcast({
        "type": "product_created",
        "data": {
            "id": product.id,
            "name": product.name,
            "price": product.price
        }
    })


async def _notify_product_updated(product: Product):
    message = {
        "action": "updated",
        "product_id": product.id,
        "product_name": product.name,
        "price": product.price
    }

    await nats_client.publish("items.updates", message)

    await manager.broadcast({
        "type": "product_updated",
        "data": {
            "id": product.id,
            "name": product.name,
            "price": product.price
        }
    })


async def _notify_product_deleted(product_id: int):
    message = {
        "action": "deleted",
        "product_id": product_id
    }

    await nats_client.publish("items.updates", message)

    await manager.broadcast({
        "type": "product_deleted",
        "data": {"id": product_id}
    })


async def _notify_all_products_deleted(count: int):
    message = {
        "action": "deleted_all",
        "count": count
    }

    await nats_client.publish("items.updates", message)

    await manager.broadcast({
        "type": "all_products_deleted",
        "data": {
            "count": count,
            "message": f"All {count} products have been deleted"
        }
    })