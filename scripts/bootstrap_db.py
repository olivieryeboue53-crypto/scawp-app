"""One-time setup: creates the SQLite schema and seeds the Directeur/ADG accounts.

Run with: uv run python scripts/bootstrap_db.py

Reads account identities (usernames, full names) from .streamlit/secrets.toml —
never from source code. Temporary passwords are generated randomly and printed
to stdout once, for secure out-of-band handoff; they are never stored in
plaintext or logged anywhere. Each account must change its password on first
login.
"""

import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scawp import auth, db  # noqa: E402
from scawp.config import get_bootstrap_accounts  # noqa: E402
from scawp.models import users as users_model  # noqa: E402


def main() -> None:
    db.init_schema()

    created = []
    for account in get_bootstrap_accounts():
        if users_model.get_by_username(account["username"]) is not None:
            print(f"Compte déjà existant, ignoré : {account['username']}")
            continue
        temp_password = secrets.token_urlsafe(12)
        users_model.create_user(
            username=account["username"],
            full_name=account["full_name"],
            password_hash=auth.hash_password(temp_password),
        )
        created.append((account["username"], temp_password))

    if not created:
        print("Aucun nouveau compte créé.")
        return

    print("\nComptes créés — transmettez ces mots de passe temporaires de façon sécurisée")
    print("(ils ne seront plus jamais affichés) :\n")
    for username, temp_password in created:
        print(f"  {username} : {temp_password}")
    print("\nChaque compte devra changer son mot de passe à la première connexion.")


if __name__ == "__main__":
    main()
