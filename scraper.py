import aiohttp
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
import logging

BASE_URL = "https://svarnoy.ru"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize a global list to hold product data
product_data = []
urls_found = 0
urls_fetched = 0

async def fetch_elements(session, url):
    if url[-1] == ':':
        url = url[:-1]
    logging.info(f"Fetching elements URL: {url}")
    async with session.get(url) as response:
        return await response.text()


async def fetch_product(session, url):
    if url[-1] == ':':
        url = url[:-1]
    global urls_found
    urls_found += 1
    logging.info(f"[{urls_found}]Fetching products URL: {url}")
    async with session.get(url) as response:
        return await response.text()

async def fetch_catalog(session, url):
    if url[-1] == ':':
        url = url[:-1]
    logging.info(f"Fetching catalog URL: {url}")
    async with session.get(url) as response:
        return await response.text()

async def parse_catalog(session, url):
    content = await fetch_elements(session, url)
    soup = BeautifulSoup(content, 'html.parser')
    product_links = [BASE_URL + a['href'] for a in soup.select('.image a')]
    logging.info(f"Found {len(product_links)} products in catalog.")
    return product_links

async def parse_pagination(session, url):
    page = 1
    product_links = []
    new_links = []
    prev_num_links = 48 # TODO: think about how to not hardcode it
    while True: 
        paged_url = f"{url}?PAGEN_1={page}"
        content = await fetch_catalog(session, paged_url)
        soup = BeautifulSoup(content, 'html.parser')
        new_links = [BASE_URL + a['href'] for a in soup.select('a.thumb')]
        product_links.extend(new_links)
        logging.info(f"Found {len(new_links)} products on page {page} of {url}.")
        if len(new_links) < prev_num_links: # TODO: Think about more complex restriction
            break
        page += 1
    return product_links

async def parse_product(session, url):
    try:
        content = await fetch_product(session, url)
        soup = BeautifulSoup(content, 'html.parser')
        name = soup.select_one('h1').text.strip()
        articul = soup.select_one('.left_block span[itemprop="value"]').text.strip()
        description = ' '.join([div.text.strip() for div in soup.select('.char > div')])
        image = BASE_URL + soup.select_one('img.product-detail-gallery__picture')['src']
        product_info = {"name": name, "articul": articul, "description": description, "image": image}
        global urls_fetched
        urls_fetched += 1
        logging.info(f"[{urls_fetched} out of {urls_found}] Parsed product: {name}")
        
        # Append product data to the global list
        product_data.append(product_info)
    except Exception as e:
        logging.error(f"Error parsing product at {url}: {e}")

async def main():
    try:
        async with aiohttp.ClientSession() as session:
            catalog_url = f"{BASE_URL}/catalog/"
            logging.info("Starting catalog parsing.")
            product_links = await parse_catalog(session, catalog_url)
            all_product_links = []
            
            for product_link in product_links:
                paginated_links = await parse_pagination(session, product_link)
                all_product_links.extend(paginated_links)
            
            logging.info(f"Found a total of {len(all_product_links)} product pages.")
            tasks = [parse_product(session, link) for link in all_product_links]
            await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(f"Error in main function: {e}")
    finally:
        # Save to Excel
        df = pd.DataFrame(product_data)
        df.to_excel("products.xlsx", index=False)
        logging.info("Data saved to products.xlsx")

# Run the main function
asyncio.run(main())
