"""Vue: gestion des fiches producteurs."""

from datetime import date

import pandas as pd
import streamlit as st

from scawp import auth
from scawp.models import producteurs as producteurs_model

_LIST_COLUMNS = [
    "code", "nom", "prenoms", "telephone", "localite", "parcelle",
    "superficie_ha", "date_adhesion", "actif",
]


def render() -> None:
    auth.require_login()
    st.title("Producteurs")

    tab_liste, tab_ajouter = st.tabs(["Liste des producteurs", "Ajouter un producteur"])
    with tab_ajouter:
        _render_form_ajout()
    with tab_liste:
        _render_liste()


def _render_form_ajout() -> None:
    with st.form("form_producteur_ajout", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nom = col1.text_input("Nom *")
        prenoms = col2.text_input("Prénoms")
        telephone = col1.text_input("Téléphone")
        localite = col2.text_input("Localité")
        parcelle = col1.text_input("Parcelle")
        superficie = col2.number_input("Superficie (ha)", min_value=0.0, step=0.1, value=0.0)
        piece_identite = col1.text_input("Pièce d'identité")
        date_adhesion = col2.date_input("Date d'adhésion", value=date.today(), max_value=date.today())
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Enregistrer")

    if submitted:
        user = auth.get_current_user()
        try:
            producteur_id = producteurs_model.create(
                nom=nom,
                prenoms=prenoms,
                telephone=telephone,
                localite=localite,
                parcelle=parcelle,
                superficie_ha=superficie or None,
                piece_identite=piece_identite,
                date_adhesion=date_adhesion,
                notes=notes,
                created_by=user["id"],
            )
            code = producteurs_model.get_by_id(producteur_id)["code"]
            st.success(f"Producteur enregistré (code {code}).")
        except ValueError as exc:
            st.error(str(exc))


def _render_liste() -> None:
    show_inactive = st.checkbox("Afficher les producteurs désactivés", value=False)
    rows = producteurs_model.list_all(include_inactive=show_inactive)
    if not rows:
        st.info("Aucun producteur enregistré.")
        return

    df = pd.DataFrame([dict(row) for row in rows])
    st.dataframe(df[_LIST_COLUMNS], use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Modifier / activer-désactiver un producteur")
    options = {
        f"{row['code']} — {row['nom']} {row['prenoms'] or ''}".strip(): row["id"] for row in rows
    }
    selected_label = st.selectbox("Sélectionner un producteur", list(options.keys()))
    if not selected_label:
        return

    producteur = producteurs_model.get_by_id(options[selected_label])
    with st.form("form_producteur_edit"):
        col1, col2 = st.columns(2)
        nom = col1.text_input("Nom *", value=producteur["nom"])
        prenoms = col2.text_input("Prénoms", value=producteur["prenoms"] or "")
        telephone = col1.text_input("Téléphone", value=producteur["telephone"] or "")
        localite = col2.text_input("Localité", value=producteur["localite"] or "")
        parcelle = col1.text_input("Parcelle", value=producteur["parcelle"] or "")
        superficie = col2.number_input(
            "Superficie (ha)", min_value=0.0, step=0.1, value=producteur["superficie_ha"] or 0.0
        )
        piece_identite = col1.text_input(
            "Pièce d'identité", value=producteur["piece_identite"] or ""
        )
        notes = st.text_area("Notes", value=producteur["notes"] or "")
        submitted = st.form_submit_button("Mettre à jour")

    if submitted:
        if not nom.strip():
            st.error("Le nom du producteur est obligatoire.")
        else:
            producteurs_model.update(
                producteur["id"],
                nom=nom.strip(),
                prenoms=prenoms or None,
                telephone=telephone or None,
                localite=localite or None,
                parcelle=parcelle or None,
                superficie_ha=superficie or None,
                piece_identite=piece_identite or None,
                notes=notes or None,
            )
            st.success("Producteur mis à jour.")
            st.rerun()

    col_a, _ = st.columns(2)
    if producteur["actif"]:
        if col_a.button("Désactiver ce producteur"):
            producteurs_model.set_active(producteur["id"], False)
            st.rerun()
    else:
        if col_a.button("Réactiver ce producteur"):
            producteurs_model.set_active(producteur["id"], True)
            st.rerun()
