# app/utils/storage.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

CATEGORY_DIR = os.path.join(STATIC_DIR, "category_images")
PRODUCT_DIR = os.path.join(STATIC_DIR, "product_images")
BRAND_DIR = os.path.join(STATIC_DIR, "brand_images")

def ensure_dirs():
    for d in [CATEGORY_DIR, PRODUCT_DIR, BRAND_DIR]:
        os.makedirs(d, exist_ok=True)
