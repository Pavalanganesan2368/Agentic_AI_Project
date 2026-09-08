"""Product catalog ingestion and transparent local retrieval.

The default retriever uses a persisted TF-IDF-like token index with no external
service. It can be replaced behind this class by FAISS or another vector store.
"""
from __future__ import annotations
import csv
import json
import logging
import math
import re
from collections import Counter
from pathlib import Path
from .models import Product, SearchResult

LOGGER = logging.getLogger(__name__)
STOP_WORDS = {"the", "a", "an", "for", "with", "and", "or", "to", "of", "is", "in", "on"}

def tokenize(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP_WORDS]

class ProductCatalog:
    def __init__(self, csv_path: Path, index_path: Path):
        self.csv_path = Path(csv_path)
        self.index_path = Path(index_path)
        self.products: list[Product] = []
        self._document_tokens: dict[str, Counter[str]] = {}
        self._idf: dict[str, float] = {}
        self.load()

    def load(self) -> None:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Product catalog not found: {self.csv_path}")
        with self.csv_path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        self.products = [self._parse_product(row) for row in rows]
        self._build_index()
        self._persist_index()

    @staticmethod
    def _parse_product(row: dict[str, str]) -> Product:
        specifications = {}
        for item in row.get("specifications", "").split(";"):
            if ":" in item:
                key, value = item.split(":", 1)
                specifications[key.strip()] = value.strip()
        return Product(
            product_id=row["product_id"], name=row["name"], category=row["category"],
            description=row["description"], price=float(row["price"]), rating=float(row["rating"]),
            availability=row["availability"], features=[x.strip() for x in row.get("features", "").split("|") if x.strip()],
            specifications=specifications,
        )

    def _build_index(self) -> None:
        documents = {p.product_id: tokenize(f"{p.name} {p.category} {p.description} {' '.join(p.features)}") for p in self.products}
        self._document_tokens = {key: Counter(value) for key, value in documents.items()}
        document_frequency = Counter(token for tokens in documents.values() for token in set(tokens))
        total = max(len(documents), 1)
        self._idf = {token: math.log((1 + total) / (1 + count)) + 1 for token, count in document_frequency.items()}

    def _persist_index(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"product_ids": [p.product_id for p in self.products], "terms": list(self._idf)}
        self.index_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def search(self, query: str, top_k: int = 5, min_score: float = 0.08) -> list[SearchResult]:
        if not query.strip() or not self.products:
            return []
        query_terms = Counter(tokenize(query))
        scored: list[SearchResult] = []
        for product in self.products:
            document = self._document_tokens[product.product_id]
            numerator = sum(query_terms[token] * document[token] * self._idf.get(token, 1.0) for token in query_terms)
            query_norm = math.sqrt(sum(value * value for value in query_terms.values()))
            document_norm = math.sqrt(sum((value * self._idf.get(token, 1.0)) ** 2 for token, value in document.items()))
            score = numerator / (query_norm * document_norm) if query_norm and document_norm else 0.0
            if score >= min_score:
                scored.append(SearchResult(product, round(score, 4)))
        return sorted(scored, key=lambda result: result.score, reverse=True)[:top_k]

    def get(self, product_id: str) -> Product | None:
        return next((product for product in self.products if product.product_id == product_id), None)
