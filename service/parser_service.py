import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re
import asyncio
from core.config import settings


async def parse_products(start_page: int = 1, end_page: Optional[int] = None):
    all_products = []
    page = start_page
    max_pages = end_page if end_page else 100

    print(f"Starting parser: pages {start_page} to {end_page if end_page else 'last'}")
    print(f"{'='*60}")

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        while page <= max_pages:
            try:
                if page == 1:
                    url = settings.PARSER_URL
                else:
                    url = f"{settings.PARSER_URL}&page={page}"

                response = await client.get(
                    url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
                        'Referer': 'https://best-magazin.com/',
                    }
                )
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                product_cards = soup.select('.product-layout')
                if not product_cards:
                    print(f"No products found on page {page}")
                    break

                page_products = []
                for idx, card in enumerate(product_cards, 1):
                    try:
                        name_elem = card.select_one('h4 a span[itemprop="name"]')
                        if not name_elem:
                            name_elem = card.select_one('h4 a')
                        if not name_elem:
                            continue

                        name = name_elem.get_text(strip=True)

                        link_elem = card.select_one('h4 a')
                        product_url = link_elem.get('href', '') if link_elem else ''
                        if product_url and not product_url.startswith('http'):
                            product_url = f"https://best-magazin.com{product_url}"

                        image_elem = card.select_one('img[itemprop="image"]')
                        if not image_elem:
                            image_elem = card.select_one('img')
                        image_url = image_elem.get('src', '') if image_elem else None
                        if image_url and not image_url.startswith('http'):
                            image_url = f"https://best-magazin.com{image_url}"

                        price_meta = card.select_one('meta[itemprop="price"]')
                        if not price_meta:
                            price_elem = card.select_one('.price-new')
                            if price_elem:
                                price_text = price_elem.get_text(strip=True)
                                price_numbers = re.findall(r'\d+', price_text)
                                price = float(''.join(price_numbers)) if price_numbers else 0
                            else:
                                continue
                        else:
                            price = float(price_meta.get('content', 0))

                        if price == 0:
                            continue

                        old_price = None
                        old_price_elem = card.select_one('.price-old')
                        if old_price_elem:
                            old_price_text = old_price_elem.get_text(strip=True)
                            old_price_numbers = re.findall(r'\d+', old_price_text)
                            if old_price_numbers:
                                old_price = float(''.join(old_price_numbers))

                        buy_button = card.select_one('.cart a')
                        availability = 'available' if buy_button else 'out_of_stock'

                        page_products.append({
                            'name': name,
                            'price': price,
                            'old_price': old_price,
                            'url': product_url,
                            'image_url': image_url,
                            'availability': availability
                        })

                    except Exception as e:
                        print(f"Error parsing card {idx}: {e}")
                        continue

                all_products.extend(page_products)

                if end_page and page >= end_page:
                    print(f"Reached target page {end_page}, stopping")
                    break

                page += 1
                if page <= max_pages:
                    delay = getattr(settings, 'PARSER_PAGE_DELAY', 2)
                    await asyncio.sleep(delay)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    print(f"\n Page {page} not found (404), finished parsing")
                    break
                else:
                    print(f"\n HTTP error {e.response.status_code} on page {page}")
                    break
            except Exception as e:
                print(f"\n Error on page {page}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                break

    # print(f"\n{'='*60}")
    # print(f"📊 Pages processed: {page - start_page + 1}")
    # print(f"📦 Total products: {len(all_products)}")

    return all_products
