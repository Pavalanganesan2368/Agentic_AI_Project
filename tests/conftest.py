import pytest
from src.catalog import ProductCatalog
from src.database import Database
from src.tools import SupportTools

@pytest.fixture
def services(tmp_path):
    catalog = ProductCatalog("data/products.csv", tmp_path / "index.json")
    database = Database(tmp_path / "support.db")
    tools = SupportTools(database, catalog, "data/orders.json")
    return catalog, database, tools
