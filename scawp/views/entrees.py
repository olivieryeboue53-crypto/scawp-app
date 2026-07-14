"""Vue: entrées de stock (réception de cacao par producteur)."""

from datetime import date

import pandas as pd
import streamlit as st

from scawp import auth
from scawp.models import lots as lots_model
from scawp.models import producteurs as producteurs_model

QUALITES = ["", "Grade I", "Grade II", "Grade III", "Hors norme"]


def render() -> None:
    auth.require_login()
    st.title("Entrées de stock (réception cacao)")

    producteurs_actifs = producteurs_model.list_active()
    if not producteurs_actifs:
        st.warning("Aucun producteur actif. Ajoutez d'abord un producteur.")
        return

    options = {
        f"{p['code']} — {p['nom']} {p['prenoms'] or ''}".strip(): p["id"] for p in producteurs_actifs
    }
    with st.form("form_entree", clear_on_submit=True):
        selected = st.selectbox("Producteur *", list(options.keys()))
        col1, col2 = st.columns(2)
        date_reception = col1.date_input(
            "Date de réception", value=date.today(), max_value=date.today()
        )
        poids_kg = col2.number_input("Poids (kg) *", min_value=0.0, step=1.0, value=0.0)
        qualite = col1.selectbox("Qualité", QUALITES)
        prix_unitaire = col2.number_input(
            "Prix unitaire (FCFA/kg)", min_value=0.0, step=1.0, value=0.0
        )
        observations = st.text_area("Observations")
        submitted = st.form_submit_button("Enregistrer l'entrée")

    if submitted:
        user = auth.get_current_user()
        try:
            lot_id = lots_model.create(
                producteur_id=options[selected],
                date_reception=date_reception,
                poids_kg=poids_kg,
                qualite=qualite or None,
                prix_unitaire=prix_unitaire or None,
                observations=observations,
                created_by=user["id"],
            )
            lot = lots_model.get_by_id(lot_id)
            st.success(f"Entrée enregistrée — lot {lot['numero_lot']} ({poids_kg:g} kg).")
        except ValueError as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("Derniers lots enregistrés")
    rows = lots_model.list_all()[:20]
    if rows:
        df = pd.DataFrame([dict(row) for row in rows])
        df["producteur"] = df["producteur_code"] + " — " + df["producteur_nom"]
        st.dataframe(
            df[["numero_lot", "producteur", "date_reception", "poids_kg", "qualite", "poids_restant"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Aucune entrée enregistrée.")
