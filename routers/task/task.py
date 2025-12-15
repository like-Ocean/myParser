from fastapi import APIRouter, Query
from typing import Optional
from service.parser_service import parse_products
from core.database import AsyncSessionLocal
from models.product import Product
from service.nats_client import nats_client
from service.websocket_manager import manager

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/run")
async def trigger_parser(
        start_page: int = Query(1, ge=1, description="Начальная страница парсинга"),
        end_page: Optional[int] = Query(None, ge=1, description="Конечная страница (None = до конца)")
):
    if end_page and end_page < start_page:
        return {
            "error": "end_page must be greater than or equal to start_page",
            "start_page": start_page,
            "end_page": end_page
        }

    products = await parse_products(start_page=start_page, end_page=end_page)
    if not products:
        return {
            "message": "No products found",
            "start_page": start_page,
            "end_page": end_page,
            "parsed_count": 0,
            "created_count": 0
        }

    async with AsyncSessionLocal() as session:
        created_count = 0
        updated_count = 0
        created_batch = []
        updated_batch = []

        for product_data in products:
            try:
                from sqlalchemy import select
                stmt = select(Product).where(Product.url == product_data['url'])
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    if existing.price != product_data['price']:
                        old_price = existing.price
                        existing.price = product_data['price']
                        existing.old_price = product_data.get('old_price')
                        updated_count += 1
                        
                        updated_batch.append({
                            "id": existing.id,
                            "name": existing.name,
                            "price": product_data['price'],
                            "old_price": old_price
                        })
                else:
                    new_product = Product(**product_data)
                    session.add(new_product)
                    await session.flush()
                    created_count += 1
                    
                    created_batch.append({
                        "id": new_product.id,
                        "name": new_product.name,
                        "price": product_data['price']
                    })
            except Exception as e:
                print(f"Error saving product: {e}")
                continue

        await session.commit()

        if created_batch:
            await nats_client.publish("items.updates", {
                "action": "batch_created",
                "count": len(created_batch),
                "products": created_batch[:10]
            })
            
            await manager.broadcast({
                "type": "products_batch_created",
                "data": {
                    "count": len(created_batch),
                    "products": created_batch[:10]
                }
            })

        if updated_batch:
            await nats_client.publish("items.updates", {
                "action": "batch_updated",
                "count": len(updated_batch),
                "products": updated_batch[:10]
            })
            
            await manager.broadcast({
                "type": "products_batch_updated",
                "data": {
                    "count": len(updated_batch),
                    "products": updated_batch[:10]
                }
            })

    return {
        "message": "Parser executed successfully",
        "start_page": start_page,
        "end_page": end_page,
        "parsed_count": len(products),
        "created_count": created_count,
        "updated_count": updated_count
    }
