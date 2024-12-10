import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urljoin
import pandas as pd
import logging
import time
import random

from settings import (
    BASE_CATEGORY_URL,
    PAGE_PARAM,
    CITY_STOREFRONT_MAP,
    OUTPUT_FILES,
    MIN_PRODUCTS,
    HEADERS
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler()
    ]
)


def fetch_page(url: str, storefront_id: str, page: int = 1) -> str:
    """
    Загружает HTML-страницу с учётом куки storefrontId для выбора города и пагинации.
    """
    cookies = {
        "storefrontId": storefront_id
    }
    params = {}
    if page > 1:
        params[PAGE_PARAM] = page
    full_url = f"{url}?{urlencode(params)}" if params else url
    try:
        response = requests.get(full_url, headers=HEADERS, cookies=cookies, timeout=15)
        response.raise_for_status()
        logging.info(f"Успешно загружена страница: {full_url}")
        return response.text
    except requests.HTTPError as http_err:
        logging.error(f"HTTP ошибка при загрузке страницы {full_url}: {http_err}")
        raise
    except Exception as err:
        logging.error(f"Ошибка при загрузке страницы {full_url}: {err}")
        raise


def extract_product_links(html: str) -> list:
    """
    Извлекает ссылки на страницы отдельных товаров из HTML-страницы категории.
    """
    soup = BeautifulSoup(html, 'html.parser')
    product_links = []

    # Предполагаем, что ссылки на товары находятся в тегах <a> с классом, содержащим 'product-card__name'
    link_tags = soup.find_all('a', class_=re.compile(r'product-card__name'))
    logging.info(f"Найдено {len(link_tags)} ссылок на товары на странице категории.")

    for tag in link_tags:
        href = tag.get('href')
        if href:
            full_url = urljoin("https://online.metro-cc.ru", href)
            product_links.append(full_url)

    return product_links


def parse_product_page(html: str, url: str) -> dict:
    """
    Парсит отдельную страницу товара и извлекает необходимые данные.
    """
    soup = BeautifulSoup(html, 'html.parser')
    product = {}

    try:
        # Извлечение ID товара
        id_tag = soup.find('p', itemprop='productID', class_=re.compile(r'product-page-content__article'))
        if id_tag:
            match = re.search(r'Артикул:\s*(\d+)', id_tag.text)
            product_id = match.group(1) if match else 'N/A'
        else:
            product_id = 'N/A'

        # Извлечение наименования
        # Извлечение наименования из meta тега
        name_meta_tag = soup.find('meta', itemprop='name')
        name = name_meta_tag['content'].strip() if name_meta_tag and 'content' in name_meta_tag.attrs else 'N/A'

        # Извлечение регулярной цены
        regular_price_tag = soup.find('span', class_=re.compile(r'product-price__sum-rubles'))
        regular_price = regular_price_tag.text.strip() if regular_price_tag else 'N/A'

        # Извлечение промо цены
        promo_price_tag = soup.find('span', class_=re.compile(r'product-price__sum-rubles'))
        # Предполагаем, что промо цена может быть ниже регулярной или отсутствовать
        # В предоставленном HTML примере промо цена также указана через 'product-price__sum-rubles'
        # Поэтому необходимо уточнить, как отличить регулярную и промо цены.
        # Если на странице есть отдельные блоки для регулярной и промо цен, можно извлечь их отдельно.
        # В данном случае будем считать, что первый 'product-price__sum-rubles' — регулярная цена,
        # а второй (если есть) — промо цена.

        price_sum_tags = soup.find_all('span', class_=re.compile(r'product-price__sum-rubles'))
        if len(price_sum_tags) >= 2:
            regular_price = price_sum_tags[0].text.strip()
            promo_price = price_sum_tags[1].text.strip()
        else:
            promo_price = 'N/A'

        # Извлечение бренда
        brand_tag = soup.find('span', class_=re.compile(r'product-attributes__list-item-links'))
        if brand_tag:
            brand_link = brand_tag.find('a')
            brand = brand_link.text.strip() if brand_link else 'N/A'
        else:
            brand = 'N/A'

        # Формирование словаря продукта
        product = {
            'id': product_id,
            'name': name,
            'url': url,
            'regular_price': regular_price,
            'promo_price': promo_price,
            'brand': brand
        }

    except Exception as e:
        logging.error(f"Ошибка при парсинге страницы товара {url}: {e}")

    return product


def save_to_xlsx(filepath: str, products: list):
    """
    Сохраняет товары в XLSX файл.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if not products:
        logging.warning(f"Нет данных для сохранения в файл: {filepath}")
        return
    df = pd.DataFrame(products)
    df.to_excel(filepath, index=False)
    logging.info(f"Данные успешно сохранены в файл: {filepath}")


def parse_city(city: str, storefront_id: str) -> list:
    """
    Парсит все страницы для заданного города и собирает товары.
    """
    all_products = []
    page = 1
    while True:
        logging.info(f"Парсим страницу {page} для города {city}...")
        try:
            html = fetch_page(BASE_CATEGORY_URL, storefront_id, page)
        except Exception as e:
            logging.error(f"Не удалось загрузить страницу {page} для города {city}: {e}")
            break

        product_links = extract_product_links(html)
        if not product_links:
            logging.info(f"Больше товаров не найдено на странице {page} для города {city}.")
            break

        logging.info(f"Найдено {len(product_links)} товаров на странице {page} для города {city}.")

        for link in product_links:
            try:
                logging.info(f"Парсим товар: {link}")
                product_html = fetch_page(link, storefront_id)
                product = parse_product_page(product_html, link)
                if product and product['id'] != 'N/A':
                    all_products.append(product)
                    logging.info(f"Добавлен товар: {product['name']} (ID: {product['id']})")
                else:
                    logging.debug(f"Пропущен товар по ссылке: {link}")
            except Exception as e:
                logging.error(f"Ошибка при парсинге товара {link}: {e}")
                continue

            # Проверка на минимальное количество товаров
            if len(all_products) >= MIN_PRODUCTS:
                logging.info(f"Достигнуто минимальное количество товаров ({MIN_PRODUCTS}) для города {city}.")
                break

            # Добавляем случайную задержку между запросами
            time.sleep(random.uniform(1, 3))  # Задержка от 1 до 3 секунд

        if len(all_products) >= MIN_PRODUCTS:
            break

        page += 1

    return all_products[:MIN_PRODUCTS]
