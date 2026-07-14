"""Application configuration loaded from Streamlit secrets."""

from pathlib import Path

import streamlit as st

APP_TITLE = "Traçabilité du stock de cacao"


def get_db_path() -> Path:
    configured = st.secrets.get("db", {}).get("path", "data/scawp.db")
    path = Path(configured)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_bootstrap_accounts() -> list[dict]:
    """Identity metadata (no passwords) for the accounts seeded on first run."""
    bootstrap = st.secrets.get("bootstrap", {})
    return [
        {
            "username": bootstrap["directeur_username"],
            "full_name": bootstrap["directeur_full_name"],
        },
        {
            "username": bootstrap["adg_username"],
            "full_name": bootstrap["adg_full_name"],
        },
    ]
