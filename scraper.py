import aiohttp
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
import logging

BASE_URL = "https://svarnoy.ru"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

product_data = []

async def fetch(session, url):
    logging.info(f"Fetching URL: {url}")
    async with session.get(url) as response:
        return await response.text()

async def parse_catalog(session, url):
    content = await fetch(session, url)
    soup = BeautifulSoup(content, 'html.parser')
    catalog_links = [BASE_URL + a['href'] for a in soup.select('.section_item a')]
    logging.info(f"Found {len(catalog_links)} catalog sections.")
    return catalog_links

async def parse_pagination(session, url):
    page = 1
    prev_num_links = 48  # Adjust this based on actual pagination behavior
    while True:
        paged_url = f"{url}?PAGEN_1={page}"
        content = await fetch(session, paged_url)
        soup = BeautifulSoup(content, 'html.parser')
        elements = soup.select('div.inner_wrap')

        if not elements:
            logging.info(f"No elements found on page {page}. Ending pagination.")
            break

        for element in elements:
            title = element.select_one('.item-title').text.strip() if element.select_one('.item-title') else "Название не указано"
            price_text = element.select_one('.cost > div.price_matrix_wrapper span.price_value').text.strip() if element.select_one('.cost > div.price_matrix_wrapper span.price_value') else "Цена не указана"
            price = float(price_text.replace('\xa0', '').replace(' ', '')) if price_text != "Цена не указана" else price_text
            art = element.select_one('.article_block div').text.strip().replace("Арт.:", "").strip() if element.select_one('.article_block div') else "Артикул не указан"
            measure = element.select_one('.cost > div.price_matrix_wrapper span.price_measure').text.strip().replace("/", "") if element.select_one('.cost > div.price_matrix_wrapper span.price_measure') else "Единица не указана"
            link = BASE_URL + element.select_one('a.dark_link')['href'] if element.select_one('a.dark_link') else None

            product_info = {
                "title": title,
                "price": price,
                "art": art,
                "measure": measure,
                "link": link
            }
            logging.info(f"Parsed product: {title}")

            product_data.append(product_info)

        new_links = [BASE_URL + a['href'] for a in soup.select('a.thumb')]
        if len(new_links) < prev_num_links:
            break
        page += 1

async def main():
    try:
        async with aiohttp.ClientSession() as session:
            catalog_url = f"{BASE_URL}/catalog/"
            logging.info("Starting catalog parsing.")
            catalog_links = await parse_catalog(session, catalog_url)

            for catalog_link in catalog_links:
                await parse_pagination(session, catalog_link)

    except Exception as e:
        logging.error(f"Error in main function: {e}")
    finally:
        df = pd.DataFrame(product_data)
        df.to_excel("products.xlsx", index=False)
        logging.info("Data saved to products.xlsx")

asyncio.run(main())

