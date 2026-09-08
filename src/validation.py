"""Input validation shared by UI and tools."""
import re

def validate_customer_id(customer_id: str) -> str:
    value = customer_id.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,50}", value):
        raise ValueError("Customer ID must be 3-50 letters, numbers, underscores, or hyphens.")
    return value

def validate_order_id(order_id: str) -> str:
    value = order_id.strip().upper()
    if not re.fullmatch(r"ORD-[A-Z0-9-]{4,30}", value):
        raise ValueError("Enter a valid order ID such as ORD-1001.")
    return value
