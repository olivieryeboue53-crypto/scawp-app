"""Producer ("producteur") records."""

import sqlite3
from datetime import date

from scawp import db


def create(
    nom: str,
    prenoms: str,
    telephone: str,
    localite: str,
    parcelle: str,
    superficie_ha: float | None,
    piece_identite: str,
    date_adhesion: date | None,
    notes: str,
    created_by: int,
) -> int:
    nom = nom.strip()
    if not nom:
        raise ValueError("Le nom du producteur est obligatoire.")

    with db.transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO producteurs
                (code, nom, prenoms, telephone, localite, parcelle, superficie_ha,
                 piece_identite, date_adhesion, notes, created_by)
            VALUES ('', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nom,
                prenoms or None,
                telephone or None,
                localite or None,
                parcelle or None,
                superficie_ha,
                piece_identite or None,
                date_adhesion.isoformat() if date_adhesion else None,
                notes or None,
                created_by,
            ),
        )
        producteur_id = cur.lastrowid
        code = f"P-{producteur_id:05d}"
        conn.execute("UPDATE producteurs SET code = ? WHERE id = ?", (code, producteur_id))
        return producteur_id


def update(producteur_id: int, **fields) -> None:
    if not fields:
        return
    allowed = {
        "nom", "prenoms", "telephone", "localite", "parcelle",
        "superficie_ha", "piece_identite", "date_adhesion", "notes",
    }
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Champs inconnus: {unknown}")
    set_clause = ", ".join(f"{key} = ?" for key in fields)
    params = (*fields.values(), producteur_id)
    db.execute(
        f"UPDATE producteurs SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
        params,
    )


def set_active(producteur_id: int, actif: bool) -> None:
    db.execute(
        "UPDATE producteurs SET actif = ?, updated_at = datetime('now') WHERE id = ?",
        (int(actif), producteur_id),
    )


def get_by_id(producteur_id: int) -> sqlite3.Row | None:
    return db.query_one("SELECT * FROM producteurs WHERE id = ?", (producteur_id,))


def list_all(include_inactive: bool = True) -> list[sqlite3.Row]:
    if include_inactive:
        return db.query("SELECT * FROM producteurs ORDER BY nom")
    return db.query("SELECT * FROM producteurs WHERE actif = 1 ORDER BY nom")


def list_active() -> list[sqlite3.Row]:
    return list_all(include_inactive=False)
