"""Agent tools for orders, returns, recommendations, and issue resolution."""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .catalog import ProductCatalog
from .database import Database
from .models import Product
from .validation import validate_order_id

class SupportTools:
    def __init__(self, database: Database, catalog: ProductCatalog, orders_path: Path):
        self.database = database
        self.catalog = catalog
        self.orders = json.loads(Path(orders_path).read_text(encoding="utf-8"))

    def track_order(self, customer_id: str, order_id: str) -> dict[str, Any]:
        order_id = validate_order_id(order_id)
        order = next((item for item in self.orders if item["order_id"] == order_id and item["customer_id"] == customer_id), None)
        if not order:
            raise LookupError("We could not find that order for this customer.")
        return order

    def process_return(self, customer_id: str, order_id: str, product_id: str, reason: str) -> dict[str, Any]:
        order = self.track_order(customer_id, order_id)
        item = next((item for item in order["items"] if item["product_id"] == product_id), None)
        if not item:
            raise LookupError("That product is not part of the selected order.")
        order_date = datetime.fromisoformat(order["order_date"]).date()
        if (datetime.now(timezone.utc).date() - order_date).days > 30:
            raise ValueError("This item is outside the 30-day return window.")
        ra_number = f"RA-{uuid.uuid4().hex[:8].upper()}"
        data = {"ra_number": ra_number, "customer_id": customer_id, "order_id": order_id, "product_id": product_id, "reason": reason.strip(), "status": "Requested", "refund_amount": item["price"] * item["quantity"], "instructions": "Pack the item securely and attach the prepaid label from your account. Drop it at any ParcelFast location.", "created_at": datetime.now(timezone.utc).isoformat()}
        self.database.add_return(data)
        return data

    def recommend(self, customer_id: str, query: str = "") -> list[Product]:
        history = " ".join(item["message"] for item in self.database.history(customer_id))
        results = self.catalog.search(f"{query} {history}", top_k=4)
        return [result.product for result in results]

    def log_complaint(self, customer_id: str, details: str, issue_type: str = "General") -> dict[str, Any]:
        escalated = len(details.strip()) > 180 or issue_type.lower() in {"payment", "safety", "legal"}
        complaint_id = self.database.add_complaint(customer_id, issue_type, details.strip(), escalated)
        return {"complaint_id": complaint_id, "status": "Escalated" if escalated else "Open", "escalated": escalated}
