from settings import CITY_STOREFRONT_MAP, OUTPUT_FILES, MIN_PRODUCTS
from parse_utils import parse_city, save_to_xlsx
import logging

def main():
    logging.info("Начинаем парсинг товаров с сайта METRO.")
    # Парсим для Москвы и СПб
    for city, storefront_id in CITY_STOREFRONT_MAP.items():
        logging.info(f"Парсим город: {city}")
        products = parse_city(city, storefront_id)
        if len(products) < MIN_PRODUCTS:
            logging.warning(f"Для города {city} спарсено меньше {MIN_PRODUCTS} товаров ({len(products)}). Возможно, нужно выбрать другую категорию или проверить доступность товаров.")
        outfile = OUTPUT_FILES[city]
        save_to_xlsx(f"output/{outfile}", products)
        logging.info(f"Готово для города {city}. Результат в файле: output/{outfile}\n")

    logging.info("Парсинг завершен.")

if __name__ == "__main__":
    main()
