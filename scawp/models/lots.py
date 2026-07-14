"""Stock entries ("lots" = cocoa receptions from producers)."""

import sqlite3
from datetime import date

from scawp import db

_BALANCE_SELECT = """
    SELECT l.*, p.code AS producteur_code, p.nom AS producteur_nom,
           p.prenoms AS producteur_prenoms,
           COALESCE((SELECT SUM(s.poids_kg) FROM sorties s WHERE s.lot_id = l.id), 0) AS poids_sorti,
           l.poids_kg - COALESCE((SELECT SUM(s.poids_kg) FROM sorties s WHERE s.lot_id = l.id), 0)
               AS poids_restant
    FROM lots l
    JOIN producteurs p ON p.id = l.producteur_id
"""


def create(
    producteur_id: int,
    date_reception: date,
    poids_kg: float,
    qualite: str,
    prix_unitaire: float | None,
    observations: str,
    created_by: int,
) -> int:
    if poids_kg is None or poids_kg <= 0:
        raise ValueError("Le poids doit être supérieur à zéro.")
    if date_reception > date.today():
        raise ValueError("La date de réception ne peut pas être dans le futur.")

    with db.transaction() as conn:
        producteur = conn.execute(
            "SELECT id FROM producteurs WHERE id = ? AND actif = 1", (producteur_id,)
        ).fetchone()
        if producteur is None:
            raise ValueError("Producteur introuvable ou inactif.")

        cur = conn.execute(
            """
            INSERT INTO lots
                (numero_lot, producteur_id, date_reception, poids_kg, qualite,
                 prix_unitaire, observations, created_by)
            VALUES ('', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                producteur_id,
                date_reception.isoformat(),
                poids_kg,
                qualite or None,
                prix_unitaire,
                observations or None,
                created_by,
            ),
        )
        lot_id = cur.lastrowid
        numero_lot = f"L-{date_reception.year}-{lot_id:05d}"
        conn.execute("UPDATE lots SET numero_lot = ? WHERE id = ?", (numero_lot, lot_id))
        return lot_id


def get_by_id(lot_id: int) -> sqlite3.Row | None:
    return db.query_one(_BALANCE_SELECT + " WHERE l.id = ?", (lot_id,))


def list_all() -> list[sqlite3.Row]:
    return db.query(_BALANCE_SELECT + " ORDER BY l.date_reception DESC, l.id DESC")


def list_available() -> list[sqlite3.Row]:
    """Lots with remaining stock > 0, for the sortie selector."""
    rows = db.query(_BALANCE_SELECT + " ORDER BY l.date_reception, l.id")
    return [row for row in rows if row["poids_restant"] > 0]


def stock_par_producteur() -> list[sqlite3.Row]:
    return db.query(
        """
        SELECT p.id, p.code, p.nom, p.prenoms,
               COALESCE(SUM(l.poids_kg), 0) AS poids_recu,
               COALESCE(SUM(l.poids_kg), 0) - COALESCE((
                   SELECT SUM(s.poids_kg) FROM sorties s
                   JOIN lots l2 ON l2.id = s.lot_id WHERE l2.producteur_id = p.id
               ), 0) AS stock_actuel_kg
        FROM producteurs p
        LEFT JOIN lots l ON l.producteur_id = p.id
        GROUP BY p.id
        ORDER BY p.nom
        """
    )
