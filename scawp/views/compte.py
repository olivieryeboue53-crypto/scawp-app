"""Vue: changement de mot de passe."""

from scawp import auth


def render(force_change: bool = False) -> None:
    if not force_change:
        auth.require_login()
    auth.render_change_password_form(force_change=force_change)
