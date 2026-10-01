# Changelog

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Versions selon [SemVer](https://semver.org/lang/fr/).

## [1.0.0] - 2026-10-01

### Ajouté
- `SKILL.md` : déroulé en quatre modes (audit en lecture seule, rapport priorisé, application avec
  accord et sauvegarde horodatée, mesure avant et après).
- `scripts/audit.py` : audit portable (Python 3.9+, bibliothèque standard) des skills, serveurs MCP,
  réglages de compaction, de modèle de sous-agents et d'effort, hooks `PreCompact`, `CLAUDE.md`,
  règles et sous-agents ; sortie texte ou JSON ; `--save` et `--compare` ; aucune valeur de secret
  affichée.
- `scripts/backup.py` : copie horodatée ISO avant modification.
- `docs/BONNES-PRATIQUES.md` : leviers étiquetés officiel, rapporté ou à vérifier, avec sources
  consultées le 2026-10-01 ; actions manuelles dans l'application ; workflow ; pistes écartées.
- `examples/settings.example.json` et `examples/CLAUDE.md.example`.
- Tests hors ligne des scripts et de la cohérence de la documentation ; intégration continue sous
  Linux, macOS et Windows.
