"""Vue: rapports de stock et traçabilité d'un lot."""

import pandas as pd
import streamlit as st

from scawp import auth
from scawp.models import lots as lots_model
from scawp.models import sorties as sorties_model


def render() -> None:
    auth.require_login()
    st.title("Rapports et traçabilité")

    tab_stock, tab_lot = st.tabs(["Stock par producteur", "Traçabilité d'un lot"])
    with tab_stock:
        _render_stock_par_producteur()
    with tab_lot:
        _render_tracabilite_lot()


def _render_stock_par_producteur() -> None:
    rows = lots_model.stock_par_producteur()
    if not rows:
        st.info("Aucune donnée de stock.")
        return
    df = pd.DataFrame([dict(row) for row in rows])
    st.metric("Stock total actuel (kg)", f"{df['stock_actuel_kg'].sum():g}")
    st.dataframe(
        df[["code", "nom", "prenoms", "poids_recu", "stock_actuel_kg"]],
        use_container_width=True,
        hide_index=True,
    )


def _render_tracabilite_lot() -> None:
    lots = lots_model.list_all()
    if not lots:
        st.info("Aucun lot enregistré.")
        return

    options = {
        f"{l['numero_lot']} — {l['producteur_code']} {l['producteur_nom']}": l["id"] for l in lots
    }
    selected = st.selectbox("Sélectionner un lot", list(options.keys()))
    lot = lots_model.get_by_id(options[selected])

    col1, col2, col3 = st.columns(3)
    col1.metric("Poids reçu (kg)", f"{lot['poids_kg']:g}")
    col2.metric("Poids sorti (kg)", f"{lot['poids_sorti']:g}")
    col3.metric("Stock restant (kg)", f"{lot['poids_restant']:g}")

    st.write(
        f"**Producteur :** {lot['producteur_code']} — "
        f"{lot['producteur_nom']} {lot['producteur_prenoms'] or ''}"
    )
    st.write(
        f"**Date de réception :** {lot['date_reception']}  •  "
        f"**Qualité :** {lot['qualite'] or '—'}"
    )

    st.subheader("Historique des sorties")
    sorties_rows = sorties_model.list_for_lot(lot["id"])
    if sorties_rows:
        df = pd.DataFrame([dict(row) for row in sorties_rows])
        st.dataframe(
            df[["date_sortie", "poids_kg", "destination", "motif", "reference_document"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Aucune sortie pour ce lot.")
