# Базовый URL категории для парсинга
BASE_CATEGORY_URL = "https://online.metro-cc.ru/category/ovoshchi-i-frukty/ovoshchi"

# Параметры для пагинации
PAGE_PARAM = "page"

# Сопоставление города и его storefrontId (куки), чтобы выбрать город
CITY_STOREFRONT_MAP = {
    "Москва": "00055",
    "Санкт-Петербург": "00028"
}

# Имена выходных файлов
OUTPUT_FILES = {
    "Москва": "output_moscow.xlsx",
    "Санкт-Петербург": "output_spb.xlsx"
}

# Количество товаров, которые нужно спарсить минимум
MIN_PRODUCTS = 100

# Заголовки для HTTP-запросов
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}
