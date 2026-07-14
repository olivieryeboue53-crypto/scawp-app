import streamlit as st

from scawp import auth, db
from scawp.config import APP_TITLE
from scawp.views import compte, entrees, export, producteurs, rapports, sorties

st.set_page_config(page_title=APP_TITLE, page_icon="🍫", layout="wide")
db.init_schema()

user = auth.get_current_user()
if user is None:
    auth.render_login_form()
    st.stop()

with st.sidebar:
    st.markdown(f"**{user['full_name']}**")
    if st.button("Se déconnecter"):
        auth.logout()
        st.rerun()

if user["must_change_password"]:
    compte.render(force_change=True)
    st.stop()

pg = st.navigation(
    {
        "Cacao": [
            st.Page(producteurs.render, title="Producteurs", icon="🧑‍🌾", url_path="producteurs"),
            st.Page(entrees.render, title="Entrées de stock", icon="📥", url_path="entrees"),
            st.Page(sorties.render, title="Sorties de stock", icon="📤", url_path="sorties"),
            st.Page(rapports.render, title="Rapports & traçabilité", icon="📊", url_path="rapports"),
            st.Page(export.render, title="Registre producteurs", icon="⬇️", url_path="export"),
        ],
        "Compte": [
            st.Page(lambda: compte.render(force_change=False), title="Changer le mot de passe", icon="🔑", url_path="compte"),
        ],
    }
)
pg.run()
