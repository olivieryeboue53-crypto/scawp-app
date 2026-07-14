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

# Leading characters that spreadsheet apps (Excel, LibreOffice, Sheets) treat
# as the start of a formula. Free-text fields (nom, localite, notes-derived
# columns...) are attacker-controllable, so values are defanged before being
# written into a file the admins will open outside the app. See CWE-1236.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_for_spreadsheet(df: pd.DataFrame) -> pd.DataFrame:
    # Applied to every column regardless of dtype (pandas may back text
    # columns with "object" or its own StringDtype depending on version) —
    # the isinstance() check below leaves non-string values untouched.
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].map(
            lambda v: f"'{v}" if isinstance(v, str) and v.startswith(_FORMULA_PREFIXES) else v
        )
    return df


def render() -> None:
    auth.require_login()
    st.title("Registre des producteurs")

    rows = producteurs_model.list_all(include_inactive=True)
    if not rows:
        st.info("Aucun producteur enregistré.")
        return

    df = pd.DataFrame([dict(row) for row in rows])[_COLUMNS]
    st.dataframe(df, use_container_width=True, hide_index=True)

    export_df = _sanitize_for_spreadsheet(df)

    col1, col2 = st.columns(2)
    csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
    col1.download_button(
        "Télécharger en CSV",
        data=csv_bytes,
        file_name="registre_producteurs.csv",
        mime="text/csv",
    )

    buffer = io.BytesIO()
    export_df.to_excel(buffer, index=False, engine="openpyxl")
    col2.download_button(
        "Télécharger en Excel",
        data=buffer.getvalue(),
        file_name="registre_producteurs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
