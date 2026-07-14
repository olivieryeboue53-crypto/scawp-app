"""Shared SQLite access layer.

All queries go through query()/execute()/transaction() below, which always use
parameterized (?) placeholders. No SQL in this codebase should ever be built by
string concatenation or f-strings.
"""

import sqlite3
import threading
from contextlib import contextmanager

import streamlit as st

from scawp.config import get_db_path

_LOCK = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    must_change_password INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS producteurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    nom TEXT NOT NULL,
    prenoms TEXT,
    telephone TEXT,
    localite TEXT,
    parcelle TEXT,
    superficie_ha REAL,
    piece_identite TEXT,
    date_adhesion TEXT,
    actif INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_producteurs_nom ON producteurs(nom);

CREATE TABLE IF NOT EXISTS lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_lot TEXT NOT NULL UNIQUE,
    producteur_id INTEGER NOT NULL REFERENCES producteurs(id),
    date_reception TEXT NOT NULL,
    poids_kg REAL NOT NULL CHECK (poids_kg > 0),
    qualite TEXT,
    prix_unitaire REAL,
    observations TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_lots_producteur ON lots(producteur_id);
CREATE INDEX IF NOT EXISTS idx_lots_date ON lots(date_reception);

CREATE TABLE IF NOT EXISTS sorties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id INTEGER NOT NULL REFERENCES lots(id),
    date_sortie TEXT NOT NULL,
    poids_kg REAL NOT NULL CHECK (poids_kg > 0),
    destination TEXT,
    motif TEXT,
    reference_document TEXT,
    observations TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sorties_lot ON sorties(lot_id);
CREATE INDEX IF NOT EXISTS idx_sorties_date ON sorties(date_sortie);
"""


@st.cache_resource
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_schema() -> None:
    with _LOCK:
        get_connection().executescript(SCHEMA)
        get_connection().commit()


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with _LOCK:
        return get_connection().execute(sql, params).fetchall()


def query_one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    with _LOCK:
        return get_connection().execute(sql, params).fetchone()


def execute(sql: str, params: tuple = ()) -> int:
    """Run a single write statement, commit, and return lastrowid."""
    with _LOCK:
        cur = get_connection().execute(sql, params)
        get_connection().commit()
        return cur.lastrowid


@contextmanager
def transaction():
    """Guard a read-then-write sequence with the same lock used by query()/execute(),
    so concurrent requests can't interleave between a validation read and its write."""
    _LOCK.acquire()
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _LOCK.release()
