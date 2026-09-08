"""Allow `python -m src` to provide a quick service check."""
from .config import settings
from .catalog import ProductCatalog

if __name__ == "__main__":
    settings.ensure_directories()
    catalog = ProductCatalog(settings.database_path.parent.parent / "data" / "products.csv", settings.product_index_path)
    print(f"Loaded {len(catalog.products)} products.")
