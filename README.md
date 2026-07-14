# 🍫 Traçabilité du stock de cacao

Application interne de la coopérative pour suivre le stock de cacao par producteur :
fiches producteurs, entrées de stock (réceptions), sorties de stock (ventes/expéditions)
tracées jusqu'au lot d'origine, rapports de traçabilité et registre des producteurs
téléchargeable.

### Comment lancer l'application

Prérequis : installer `uv` si ce n'est pas déjà fait.

```
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. Installer les dépendances

   ```
   $ uv sync
   ```

2. Configurer les secrets (une seule fois)

   ```
   $ cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

   Modifier `.streamlit/secrets.toml` pour y mettre les identifiants (nom d'utilisateur,
   nom complet) du Directeur et de l'ADG. Ce fichier est ignoré par git — n'y mettez
   jamais de mot de passe, ils sont générés automatiquement à l'étape suivante.

3. Initialiser la base de données et créer les deux comptes

   ```
   $ uv run python scripts/bootstrap_db.py
   ```

   Le script affiche une seule fois un mot de passe temporaire pour chaque compte.
   Transmettez-les de façon sécurisée au Directeur et à l'ADG : ils devront le
   changer dès leur première connexion.

4. Lancer l'application

   ```
   $ uv run streamlit run streamlit_app.py
   ```

### Sécurité

- Mots de passe hashés (bcrypt), jamais stockés ni transmis en clair.
- Toutes les pages nécessitent une connexion valide.
- Toutes les requêtes à la base SQLite sont paramétrées.
- Aucun secret n'est commité dans le dépôt (`.streamlit/secrets.toml` et la base
  `data/*.db` sont ignorés par git).
- Ne pas déployer avec les options `--server.enableCORS false
  --server.enableXsrfProtection false` utilisées uniquement pour le confort du
  devcontainer/Codespaces — ces protections doivent rester actives en production.
