import asyncio
from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.product import Product
from service.parser_service import parse_products
from service.nats_client import nats_client
from service.websocket_manager import manager
from core.config import settings


async def update_products_task():
    print(f"Background task started (interval: {settings.PARSER_INTERVAL_SECONDS}s)")
    while True:
        try:
            products_data = await parse_products(start_page=1, end_page=None)

            if not products_data:
                await asyncio.sleep(settings.PARSER_INTERVAL_SECONDS)
                continue

            async with AsyncSessionLocal() as session:
                updated_count = 0
                created_count = 0

                for product_data in products_data:
                    try:
                        stmt = select(Product).where(Product.url == product_data['url'])
                        result = await session.execute(stmt)
                        existing = result.scalar_one_or_none()

                        if existing:
                            if existing.price != product_data['price']:
                                old_price = existing.price
                                existing.price = product_data['price']
                                if product_data.get('old_price'):
                                    existing.old_price = product_data['old_price']
                                updated_count += 1

                                print(
                                    f"Updated: {existing.name[:50]}... ({old_price} → {product_data['price']} руб.)"
                                )

                                await nats_client.publish("items.updates", {
                                    "action": "updated",
                                    "product_id": existing.id,
                                    "product_name": existing.name,
                                    "old_price": old_price,
                                    "new_price": product_data['price']
                                })

                                await manager.broadcast({
                                    "type": "product_updated",
                                    "data": {
                                        "id": existing.id,
                                        "name": existing.name,
                                        "price": product_data['price'],
                                        "old_price": old_price
                                    }
                                })
                        else:
                            new_product = Product(**product_data)
                            session.add(new_product)
                            await session.flush()
                            created_count += 1

                            if created_count % 50 == 0:
                                print(f"Created {created_count} products so far...")

                            await nats_client.publish("items.updates", {
                                "action": "created",
                                "product_id": new_product.id,
                                "product_name": new_product.name,
                                "price": product_data['price']
                            })

                            await manager.broadcast({
                                "type": "product_created",
                                "data": {
                                    "id": new_product.id,
                                    "name": new_product.name,
                                    "price": product_data['price']
                                }
                            })
                    except Exception as e:
                        print(f"Error processing product: {e}")
                        continue

                await session.commit()
                print(f"Update completed. Created: {created_count}, Updated: {updated_count}")

        except Exception as e:
            print(f"Error in background task: {e}")

        await asyncio.sleep(settings.PARSER_INTERVAL_SECONDS)
