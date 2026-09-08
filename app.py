"""Streamlit dashboard for the AI E-Commerce Customer Support Agent."""
import logging
import streamlit as st
from src.agent import SupportAgent
from src.catalog import ProductCatalog
from src.config import settings
from src.database import Database
from src.tools import SupportTools

logging.basicConfig(level=settings.log_level)
settings.ensure_directories()
catalog = ProductCatalog(settings.database_path.parent.parent / "data" / "products.csv", settings.product_index_path)
database = Database(settings.database_path)
tools = SupportTools(database, catalog, settings.database_path.parent.parent / "data" / "orders.json")
agent = SupportAgent(database, catalog, tools)

st.set_page_config(page_title=settings.app_name, page_icon="🛍️", layout="wide")
st.title("AI E-Commerce Customer Support")
st.caption("Product search, order support, returns, and recommendations in one workspace.")

with st.sidebar:
    st.header("Customer")
    customer_id = st.text_input("Customer ID", value="demo-user")
    page = st.radio("Navigate", ["Home", "Product Search", "Track Order", "Return Request", "My Account", "Chat Support"])
    st.divider()
    st.caption("Local demo mode: catalog retrieval and tools work without external API credentials.")

def product_card(product):
    with st.container(border=True):
        st.subheader(product.name)
        st.write(product.description)
        st.write(f"**${product.price:,.2f}**  |  {product.rating}/5  |  **{product.availability}**")
        st.caption("Features: " + ", ".join(product.features))

if page == "Home":
    customer = database.customer(customer_id)
    st.header(f"Welcome back, {customer['name']}")
    a, b, c = st.columns(3)
    a.metric("Loyalty tier", customer["tier"])
    b.metric("Points", customer["loyalty_points"])
    c.metric("Saved interactions", len(database.history(customer_id)))
    st.subheader("Recommended for you")
    for product in tools.recommend(customer_id, "popular everyday products")[:3]: product_card(product)
    st.subheader("Quick actions")
    st.info("Use the sidebar to search products, track ORD-1001, request a return, or chat with support.")
elif page == "Product Search":
    st.header("Product Search")
    query = st.text_input("What are you looking for?", placeholder="wireless headphones for commuting")
    max_price = st.slider("Maximum price", 0, 2000, 2000, step=25)
    if query:
        results = [result for result in catalog.search(query) if result.product.price <= max_price]
        st.caption(f"{len(results)} catalog result(s)")
        for result in results: product_card(result.product)
elif page == "Track Order":
    st.header("Track Order")
    order_id = st.text_input("Order ID", placeholder="ORD-1001")
    if st.button("Track", type="primary") and order_id:
        try:
            order = tools.track_order(customer_id, order_id)
            st.success(f"{order['order_id']} is {order['status']}.")
            st.write(f"Items: {', '.join(item['name'] for item in order['items'])}")
            st.write(f"Carrier: {order['carrier']} | Tracking: {order['tracking_number'] or 'Not assigned'} | ETA: {order['estimated_delivery']}")
        except (LookupError, ValueError) as error: st.error(str(error))
elif page == "Return Request":
    st.header("Return Request")
    order_id = st.text_input("Order ID")
    product_id = st.text_input("Product ID", placeholder="P100")
    reason = st.selectbox("Reason", ["Defective", "Wrong item", "Changed mind", "Arrived late"])
    if st.button("Create return request", type="primary"):
        try:
            result = tools.process_return(customer_id, order_id, product_id, reason)
            st.success(f"Return {result['ra_number']} created.")
            st.write(result["instructions"])
        except (LookupError, ValueError) as error: st.error(str(error))
elif page == "My Account":
    st.header("My Account")
    st.json(database.customer(customer_id))
    st.subheader("Return history")
    st.dataframe(database.returns(customer_id), use_container_width=True)
    st.subheader("Conversation history")
    for item in database.history(customer_id): st.chat_message(item["role"]).write(item["message"])
elif page == "Chat Support":
    st.header("Chat Support")
    if "messages" not in st.session_state: st.session_state.messages = []
    for message in st.session_state.messages: st.chat_message(message["role"]).write(message["content"])
    prompt = st.chat_input("Ask about a product, order, return, or recommendation")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = agent.respond(customer_id, prompt)
        st.session_state.messages.append({"role": "assistant", "content": response.message})
        st.rerun()
