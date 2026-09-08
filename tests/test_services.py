from src.agent import SupportAgent
from src.validation import validate_order_id

def test_product_retrieval(services):
    catalog, _, _ = services
    results = catalog.search("noise cancelling headphones")
    assert results
    assert results[0].product.product_id == "P100"
    assert results[0].product.price == 129.99

def test_order_tracking(services):
    _, _, tools = services
    order = tools.track_order("demo-user", "ord-1001")
    assert order["status"] == "shipped"
    assert order["tracking_number"]

def test_return_processing_persists(services):
    _, database, tools = services
    result = tools.process_return("demo-user", "ORD-1001", "P100", "Defective")
    assert result["ra_number"].startswith("RA-")
    assert database.returns("demo-user")[0]["status"] == "Requested"

def test_recommendations_use_catalog(services):
    _, database, tools = services
    database.save_interaction("demo-user", "user", "I need wireless audio")
    products = tools.recommend("demo-user")
    assert products
    assert all(product.price >= 0 for product in products)

def test_agent_routes_and_persists(services):
    catalog, database, tools = services
    agent = SupportAgent(database, catalog, tools)
    response = agent.respond("demo-user", "Where is ORD-1001?")
    assert response.intent == "order_status"
    assert "shipped" in response.message
    assert len(database.history("demo-user")) == 2

def test_invalid_order_id():
    try:
        validate_order_id("bad id")
        assert False
    except ValueError:
        pass
