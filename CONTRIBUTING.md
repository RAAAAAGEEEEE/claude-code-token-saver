# Contribuer

Issues et pull requests bienvenues.

## Avant d'ouvrir une pull request

1. `python -m unittest discover -s tests` passe (hors ligne, bibliothèque standard seulement).
2. Tout constat ajouté à `scripts/audit.py` a un test dans `tests/test_audit.py` et cite une **page
   de documentation officielle** (champ `source`) ; un conseil de blog est étiqueté « rapporté » dans
   `docs/BONNES-PRATIQUES.md` et ne devient pas un constat.
3. Toute affirmation ajoutée dans `docs/BONNES-PRATIQUES.md` porte son étiquette (officiel, rapporté, à
   vérifier), sa source et la date de consultation. Aucun chiffre d'économie sans mesure citée.
4. L'audit n'imprime jamais de valeur sensible : toute nouvelle clé lue est ajoutée à la liste blanche
   de [docs/CONFIGURATION.md](docs/CONFIGURATION.md) et le test `test_output_never_contains_secrets`
   reste vert.
5. La documentation change **dans le même commit** que le comportement : `SKILL.md` si le déroulé
   change, `docs/` si l'usage ou la configuration change, `CHANGELOG.md` dans tous les cas.
6. Aucun tiret cadratin dans les fichiers du dépôt (un test le vérifie).
7. Aucune donnée personnelle ni nom de projet réel dans les exemples, fixtures et tests : tout est
   fictif et dit comme tel.

## Revérifier les leviers

Quand Claude Code publie une nouvelle version majeure : relire les pages listées dans
`docs/BONNES-PRATIQUES.md`, corriger ce qui a changé, mettre à jour la date « vérifié le » dans
`SKILL.md`, `README.md`, `scripts/audit.py` (`DOCS_DATE`) et `CHANGELOG.md`.

## Style

- Documentation et messages en français ; code et noms de variables en anglais.
- Python 3.9 ou plus récent, bibliothèque standard uniquement.
