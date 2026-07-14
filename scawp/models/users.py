"""User account queries."""

import sqlite3

from scawp import db


def get_by_username(username: str) -> sqlite3.Row | None:
    return db.query_one(
        "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
    )


def get_by_id(user_id: int) -> sqlite3.Row | None:
    return db.query_one(
        "SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,)
    )


def create_user(username: str, full_name: str, password_hash: str) -> int:
    return db.execute(
        """
        INSERT INTO users (username, full_name, password_hash, must_change_password)
        VALUES (?, ?, ?, 1)
        """,
        (username, full_name, password_hash),
    )


def set_password(user_id: int, password_hash: str, must_change_password: bool = False) -> None:
    db.execute(
        """
        UPDATE users
        SET password_hash = ?, must_change_password = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (password_hash, int(must_change_password), user_id),
    )
