"""Stock exits ("sorties") — sales/shipments traced back to a single lot each."""

import sqlite3
from datetime import date

from scawp import db


def create(
    lot_id: int,
    date_sortie: date,
    poids_kg: float,
    destination: str,
    motif: str,
    reference_document: str,
    observations: str,
    created_by: int,
) -> int:
    if poids_kg is None or poids_kg <= 0:
        raise ValueError("Le poids sorti doit être supérieur à zéro.")
    if date_sortie > date.today():
        raise ValueError("La date de sortie ne peut pas être dans le futur.")

    with db.transaction() as conn:
        lot = conn.execute(
            """
            SELECT l.id, l.date_reception, l.poids_kg,
                   l.poids_kg - COALESCE((SELECT SUM(s.poids_kg) FROM sorties s WHERE s.lot_id = l.id), 0)
                       AS poids_restant
            FROM lots l WHERE l.id = ?
            """,
            (lot_id,),
        ).fetchone()
        if lot is None:
            raise ValueError("Lot introuvable.")
        if date_sortie.isoformat() < lot["date_reception"]:
            raise ValueError("La date de sortie ne peut pas précéder la date de réception du lot.")
        if poids_kg > lot["poids_restant"]:
            raise ValueError(
                f"Quantité supérieure au stock restant du lot "
                f"({lot['poids_restant']:g} kg disponible)."
            )

        cur = conn.execute(
            """
            INSERT INTO sorties
                (lot_id, date_sortie, poids_kg, destination, motif,
                 reference_document, observations, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lot_id,
                date_sortie.isoformat(),
                poids_kg,
                destination or None,
                motif or None,
                reference_document or None,
                observations or None,
                created_by,
            ),
        )
        return cur.lastrowid


def list_for_lot(lot_id: int) -> list[sqlite3.Row]:
    return db.query(
        "SELECT * FROM sorties WHERE lot_id = ? ORDER BY date_sortie, id", (lot_id,)
    )


def list_all() -> list[sqlite3.Row]:
    return db.query(
        """
        SELECT s.*, l.numero_lot, p.code AS producteur_code, p.nom AS producteur_nom,
               p.prenoms AS producteur_prenoms
        FROM sorties s
        JOIN lots l ON l.id = s.lot_id
        JOIN producteurs p ON p.id = l.producteur_id
        ORDER BY s.date_sortie DESC, s.id DESC
        """
    )
