"""Authentication: password hashing, session handling, login/logout, password change."""

import time

import bcrypt
import streamlit as st

from scawp.models import users as users_model

SESSION_KEY = "auth_user_id"
_FAILED_ATTEMPTS_KEY = "auth_failed_attempts"
_LOCKOUT_UNTIL_KEY = "auth_lockout_until"
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 60

# Used to keep the timing of a login against an unknown username close to a
# real check, so usernames can't be enumerated by response latency.
_DUMMY_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_current_user():
    user_id = st.session_state.get(SESSION_KEY)
    if user_id is None:
        return None
    return users_model.get_by_id(user_id)


def _is_locked_out() -> float:
    """Return seconds remaining in lockout, or 0 if not locked out."""
    until = st.session_state.get(_LOCKOUT_UNTIL_KEY, 0)
    remaining = until - time.time()
    return max(0.0, remaining)


def _register_failed_attempt() -> None:
    attempts = st.session_state.get(_FAILED_ATTEMPTS_KEY, 0) + 1
    st.session_state[_FAILED_ATTEMPTS_KEY] = attempts
    if attempts >= _MAX_ATTEMPTS:
        st.session_state[_LOCKOUT_UNTIL_KEY] = time.time() + _LOCKOUT_SECONDS
        st.session_state[_FAILED_ATTEMPTS_KEY] = 0


def attempt_login(username: str, password: str) -> bool:
    user = users_model.get_by_username(username.strip())
    if user is None:
        verify_password(password, _DUMMY_HASH)  # constant-time-ish decoy
        _register_failed_attempt()
        return False
    if not verify_password(password, user["password_hash"]):
        _register_failed_attempt()
        return False
    st.session_state[_FAILED_ATTEMPTS_KEY] = 0
    st.session_state[SESSION_KEY] = user["id"]
    return True


def logout() -> None:
    st.session_state.clear()


def change_password(user_id: int, current_password: str, new_password: str) -> str | None:
    """Returns an error message, or None on success."""
    user = users_model.get_by_id(user_id)
    if user is None or not verify_password(current_password, user["password_hash"]):
        return "Mot de passe actuel incorrect."
    if len(new_password) < 10:
        return "Le nouveau mot de passe doit contenir au moins 10 caractères."
    if new_password == current_password:
        return "Le nouveau mot de passe doit être différent de l'ancien."
    users_model.set_password(user_id, hash_password(new_password), must_change_password=False)
    return None


def require_login() -> None:
    """Defense-in-depth guard called at the top of every view. The primary gate
    lives in streamlit_app.py, which never constructs these views pre-auth."""
    if get_current_user() is None:
        st.error("Veuillez vous connecter.")
        st.stop()


def render_login_form() -> None:
    st.title("Connexion")
    remaining = _is_locked_out()
    if remaining > 0:
        st.warning(f"Trop de tentatives échouées. Réessayez dans {int(remaining) + 1} secondes.")
        return

    with st.form("login_form"):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")

    if submitted:
        if attempt_login(username, password):
            st.rerun()
        else:
            st.error("Identifiant ou mot de passe incorrect.")


def render_change_password_form(force_change: bool = False) -> None:
    st.title("Changer le mot de passe")
    if force_change:
        st.info("Vous devez définir un nouveau mot de passe avant de continuer.")

    user = get_current_user()
    with st.form("change_password_form"):
        current_password = st.text_input("Mot de passe actuel", type="password")
        new_password = st.text_input("Nouveau mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le nouveau mot de passe", type="password")
        submitted = st.form_submit_button("Valider")

    if submitted:
        if new_password != confirm_password:
            st.error("Les deux mots de passe ne correspondent pas.")
            return
        error = change_password(user["id"], current_password, new_password)
        if error:
            st.error(error)
        else:
            st.success("Mot de passe mis à jour.")
            st.rerun()
