"""SQLite persistence for customer memory, orders, returns, and complaints."""
from __future__ import annotations
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY, name TEXT NOT NULL, contact TEXT DEFAULT '',
                tier TEXT DEFAULT 'Standard', loyalty_points INTEGER DEFAULT 0,
                preferences TEXT DEFAULT '[]', created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT NOT NULL,
                role TEXT NOT NULL, message TEXT NOT NULL, intent TEXT DEFAULT '', created_at TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
            );
            CREATE TABLE IF NOT EXISTS returns (
                ra_number TEXT PRIMARY KEY, customer_id TEXT NOT NULL, order_id TEXT NOT NULL,
                product_id TEXT NOT NULL, reason TEXT NOT NULL, status TEXT NOT NULL,
                refund_amount REAL NOT NULL, instructions TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT NOT NULL,
                issue_type TEXT NOT NULL, details TEXT NOT NULL, status TEXT NOT NULL,
                escalated INTEGER DEFAULT 0, created_at TEXT NOT NULL
            );
            """)

    def ensure_customer(self, customer_id: str, name: str = "Demo Customer", contact: str = "") -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            connection.execute("INSERT OR IGNORE INTO customers(customer_id,name,contact,created_at) VALUES(?,?,?,?)", (customer_id, name, contact, now))

    def save_interaction(self, customer_id: str, role: str, message: str, intent: str = "") -> None:
        self.ensure_customer(customer_id)
        with self.connect() as connection:
            connection.execute("INSERT INTO interactions(customer_id,role,message,intent,created_at) VALUES(?,?,?,?,?)", (customer_id, role, message, intent, datetime.now(timezone.utc).isoformat()))

    def history(self, customer_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM interactions WHERE customer_id=? ORDER BY id DESC LIMIT ?", (customer_id, limit)).fetchall()
        return [dict(row) for row in reversed(rows)]

    def customer(self, customer_id: str) -> dict[str, Any]:
        self.ensure_customer(customer_id)
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM customers WHERE customer_id=?", (customer_id,)).fetchone()
        result = dict(row)
        result["preferences"] = json.loads(result["preferences"] or "[]")
        return result

    def add_return(self, data: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute("INSERT INTO returns VALUES(?,?,?,?,?,?,?,?,?)", tuple(data[key] for key in ("ra_number", "customer_id", "order_id", "product_id", "reason", "status", "refund_amount", "instructions", "created_at")))

    def returns(self, customer_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM returns WHERE customer_id=? ORDER BY created_at DESC", (customer_id,)).fetchall()]

    def add_complaint(self, customer_id: str, issue_type: str, details: str, escalated: bool) -> int:
        with self.connect() as connection:
            cursor = connection.execute("INSERT INTO complaints(customer_id,issue_type,details,status,escalated,created_at) VALUES(?,?,?,?,?,?)", (customer_id, issue_type, details, "Escalated" if escalated else "Open", int(escalated), datetime.now(timezone.utc).isoformat()))
            return int(cursor.lastrowid)
