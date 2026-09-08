"""Intent routing and response generation for the support agent."""
from __future__ import annotations
import re
from .catalog import ProductCatalog
from .database import Database
from .models import AgentResponse
from .tools import SupportTools

class SupportAgent:
    def __init__(self, database: Database, catalog: ProductCatalog, tools: SupportTools):
        self.database, self.catalog, self.tools = database, catalog, tools

    @staticmethod
    def detect_intent(message: str) -> str:
        text = message.lower()
        if re.search(r"\bord-[a-z0-9-]+\b", text): return "order_status"
        if any(word in text for word in ("return", "refund", "send back")): return "return_request"
        if any(word in text for word in ("order", "track", "delivery", "shipped")): return "order_status"
        if any(word in text for word in ("recommend", "suggest", "similar")): return "recommendation"
        if any(word in text for word in ("complaint", "broken", "problem", "issue")): return "complaint"
        if any(word in text for word in ("shipping", "carrier", "delivery time")): return "shipping"
        return "product_search"

    def respond(self, customer_id: str, message: str) -> AgentResponse:
        intent = self.detect_intent(message)
        self.database.save_interaction(customer_id, "user", message, intent)
        try:
            if intent == "order_status":
                match = re.search(r"ORD-[A-Z0-9-]+", message.upper())
                if not match: return AgentResponse(intent, "Please provide an order ID such as ORD-1001.")
                order = self.tools.track_order(customer_id, match.group())
                response = AgentResponse(intent, f"Order {order['order_id']} is {order['status']}. Estimated delivery: {order['estimated_delivery']}.", {"order": order})
            elif intent == "recommendation":
                products = self.tools.recommend(customer_id, message)
                response = AgentResponse(intent, self._product_message(products), {"products": products})
            elif intent == "complaint":
                result = self.tools.log_complaint(customer_id, message)
                response = AgentResponse(intent, f"Your issue has been logged as complaint {result['complaint_id']}. Status: {result['status']}.", result)
            else:
                results = self.catalog.search(message)
                response = AgentResponse(intent, self._product_message([result.product for result in results]), {"matches": len(results)}, results)
        except (LookupError, ValueError) as error:
            response = AgentResponse(intent, str(error))
        self.database.save_interaction(customer_id, "assistant", response.message, intent)
        return response

    @staticmethod
    def _product_message(products) -> str:
        if not products: return "I couldn't find a matching product in the catalog. Please try another description or ask for a human agent."
        return "Here are the catalog matches: " + "; ".join(f"{p.name} (${p.price:.2f}, {p.availability})" for p in products)
