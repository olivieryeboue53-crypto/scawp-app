"""Vue: sorties de stock (ventes / expéditions), tracées jusqu'au lot d'origine."""

from datetime import date

import pandas as pd
import streamlit as st

from scawp import auth
from scawp.models import lots as lots_model
from scawp.models import sorties as sorties_model

MOTIFS = ["Vente", "Transport", "Transformation", "Autre"]


def render() -> None:
    auth.require_login()
    st.title("Sorties de stock (ventes / expéditions)")

    lots_disponibles = lots_model.list_available()
    if not lots_disponibles:
        st.warning("Aucun lot avec du stock disponible.")
        return

    options = {
        f"{l['numero_lot']} — {l['producteur_code']} {l['producteur_nom']} "
        f"— {l['poids_restant']:g} kg disponibles": l["id"]
        for l in lots_disponibles
    }
    with st.form("form_sortie", clear_on_submit=True):
        selected = st.selectbox("Lot *", list(options.keys()))
        col1, col2 = st.columns(2)
        date_sortie = col1.date_input("Date de sortie", value=date.today(), max_value=date.today())
        poids_kg = col2.number_input("Poids sorti (kg) *", min_value=0.0, step=1.0, value=0.0)
        destination = col1.text_input("Destination / acheteur")
        motif = col2.selectbox("Motif", MOTIFS)
        reference_document = col1.text_input("Référence document (bon, facture...)")
        observations = st.text_area("Observations")
        submitted = st.form_submit_button("Enregistrer la sortie")

    if submitted:
        user = auth.get_current_user()
        try:
            sorties_model.create(
                lot_id=options[selected],
                date_sortie=date_sortie,
                poids_kg=poids_kg,
                destination=destination,
                motif=motif,
                reference_document=reference_document,
                observations=observations,
                created_by=user["id"],
            )
            st.success("Sortie enregistrée.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("Dernières sorties enregistrées")
    rows = sorties_model.list_all()[:20]
    if rows:
        df = pd.DataFrame([dict(row) for row in rows])
        df["producteur"] = df["producteur_code"] + " — " + df["producteur_nom"]
        st.dataframe(
            df[["numero_lot", "producteur", "date_sortie", "poids_kg", "destination", "motif"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Aucune sortie enregistrée.")
