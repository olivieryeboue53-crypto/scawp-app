"""Vue: registre des producteurs téléchargeable."""

import io

import pandas as pd
import streamlit as st

from scawp import auth
from scawp.models import producteurs as producteurs_model

_COLUMNS = [
    "code", "nom", "prenoms", "telephone", "localite", "parcelle",
    "superficie_ha", "piece_identite", "date_adhesion", "actif",
]


def render() -> None:
    auth.require_login()
    st.title("Registre des producteurs")

    rows = producteurs_model.list_all(include_inactive=True)
    if not rows:
        st.info("Aucun producteur enregistré.")
        return

    df = pd.DataFrame([dict(row) for row in rows])[_COLUMNS]
    st.dataframe(df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    col1.download_button(
        "Télécharger en CSV",
        data=csv_bytes,
        file_name="registre_producteurs.csv",
        mime="text/csv",
    )

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    col2.download_button(
        "Télécharger en Excel",
        data=buffer.getvalue(),
        file_name="registre_producteurs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
