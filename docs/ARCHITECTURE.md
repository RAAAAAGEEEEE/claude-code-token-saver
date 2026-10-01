# Architecture

## Principe : divulgation progressive

Claude lit `SKILL.md` à chaque déclenchement : il reste court (périmètre, règles dures, déroulé en
quatre modes). Le détail des leviers est dans `docs/BONNES-PRATIQUES.md`, lu seulement quand il sert.

```
claude-code-token-saver/
├── SKILL.md                      déroulé, règles dures, exemple de rapport
├── scripts/
│   ├── audit.py                  audit en lecture seule, comparaison avant et après
│   └── backup.py                 copie horodatée avant modification
├── examples/
│   ├── settings.example.json     réglages génériques
│   ├── CLAUDE.md.example         paragraphe générique
│   └── agents/                   quatre définitions d'agents (executant, analyste, expert, trieur)
├── docs/                         documentation humaine (leviers, usage, limites…)
├── tests/                        tests des scripts et cohérence de la documentation
└── .github/workflows/tests.yml   tests sous Linux, macOS et Windows
```

## Déroulé

1. **Audit** : `audit.py` lit les fichiers de configuration (liste blanche de clés, jamais de valeurs
   sensibles), mesure et produit des constats ; sortie texte ou JSON.
2. **Rapport** : Claude présente les constats, complétés par `/context` et `/usage` collés par
   l'utilisateur.
3. **Application** : après accord, `backup.py` puis édition minimale du fichier par Claude, avec
   validation du JSON.
4. **Mesure** : nouvelle session, `audit.py --compare`, `/context`, `/usage`.

## Pourquoi un script en plus des consignes

Une consigne de prompt ne mesure rien et ne garantit pas la confidentialité : un modèle peut recopier
un champ sensible en lisant `settings.json`. Le script ne lit que des champs listés, imprime des noms et
des nombres, et ses tests vérifient qu'aucun secret fictif ne sort. Il donne aussi des mesures
reproductibles pour la comparaison.

## Modules de `audit.py`

| Fonction | Rôle |
|---|---|
| `collect_settings`, `setting`, `env_value` | lecture des trois `settings.json` et des variables surveillées |
| `collect_skills` | skills utilisateur, projet et synchronisés ; taille du listing avec `skillOverrides` |
| `collect_mcp` | noms des serveurs (`.claude.json`, `.mcp.json`), serveurs désactivés du projet |
| `collect_memory_files`, `collect_rules`, `collect_agents`, `collect_hooks` | `CLAUDE.md`, règles, sous-agents, événements de hooks |
| `analyse` | assemble les mesures et les constats |
| `render_text`, `render_compare` | rapport lisible et comparaison |

Voir aussi : [USAGE.md](USAGE.md), [LIMITATIONS.md](LIMITATIONS.md).
