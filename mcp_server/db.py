import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

# Path to the SQLite database created by database_setup.py
DB_PATH = Path(__file__).with_name("support.db")

def get_connection():
    """
    Open a new SQLite connection.
    Each function uses its own connection via context managers.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn

def _row_to_dict(row: Optional[sqlite3.Row]):
    """Convert a sqlite Row to a plain dict (or None)."""
    return dict(row) if row is not None else None

# Customer Tool Functions
def get_customer(customer_id: int):
    """Return a single customer by id, or None if not found."""
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM customers WHERE id = ?",
            (customer_id,),
        )
        row = cur.fetchone()
        return _row_to_dict(row)

def list_customers(status: Optional[str] = None, limit: int = 10):
    """Return a list of customers, optionally filtered by status."""
    with get_connection() as conn:
        if status:
            cur = conn.execute(
                "SELECT * FROM customers WHERE status = ? ORDER BY id LIMIT ?",
                (status, limit),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM customers ORDER BY id LIMIT ?",
                (limit,),
            )
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def update_customer(customer_id: int, data: Dict[str, Any]):
    """
    Update a customer with the provided fields in `data`.
    Returns the updated customer row as a dict.
    """
    # Only allow safe, known fields to be updated
    fields = [k for k in data.keys() if k in {"name", "email", "phone", "status"}]
    if not fields:
        raise ValueError("No valid fields to update.")

    set_clause = ", ".join(f"{field} = ?" for field in fields)
    values = [data[field] for field in fields]
    values.append(customer_id)

    with get_connection() as conn:
        conn.execute(
            f"UPDATE customers SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()

        cur = conn.execute(
            "SELECT * FROM customers WHERE id = ?",
            (customer_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Customer {customer_id} not found after update.")
        return dict(row)

# Ticket Tool Functions
def create_ticket(customer_id: int, issue: str, priority: str = "medium"):
    """
    Create a new ticket for a customer.
    Returns the created ticket row as a dict.
    """
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO tickets (customer_id, issue, priority)
            VALUES (?, ?, ?)
            """,
            (customer_id, issue, priority),
        )
        ticket_id = cur.lastrowid
        conn.commit()

        cur = conn.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,),
        )
        row = cur.fetchone()
        return dict(row)

def get_customer_history(customer_id: int):
    """
    Return all tickets for a given customer, newest first.
    """
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT * FROM tickets
            WHERE customer_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (customer_id,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
