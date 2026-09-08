"""Shared typed models for the application."""
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Product:
    product_id: str
    name: str
    category: str
    description: str
    price: float
    rating: float
    availability: str
    features: list[str] = field(default_factory=list)
    specifications: dict[str, str] = field(default_factory=dict)

@dataclass
class SearchResult:
    product: Product
    score: float

@dataclass
class AgentResponse:
    intent: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    sources: list[SearchResult] = field(default_factory=list)
