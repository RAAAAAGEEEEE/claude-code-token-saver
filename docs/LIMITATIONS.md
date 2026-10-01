# Limites

Ce skill aide à retirer le superflu et à mesurer ; il ne garantit aucune économie.

## Ce que le skill ne prouve pas

- **Aucun gain chiffré.** Anthropic ne publie pas la pondération des tokens d'entrée, de sortie et de
  cache dans le quota d'un abonnement. Les écarts affichés par `--compare` sont des écarts de
  **contexte estimé**, pas des économies de quota démontrées. Seules `/usage` et votre expérience, sur
  des tâches comparables, le disent.
- **Pas d'évaluation automatique du comportement de Claude** avec le skill (déclenchement, qualité du
  rapport). Seuls les scripts sont testés.
- Les leviers « rapportés » (articles tiers) ne sont pas mesurés ici.

## Ce que l'audit ne voit pas

- Les **connecteurs claude.ai**, les serveurs MCP **intégrés à l'application** et ceux fournis par des
  **plugins** : ils ne sont pas dans les fichiers lus. Utilisez `/mcp` et `/context`.
- Les **skills de plugins** et les skills fournis par une organisation.
- Les **réglages gérés** par une organisation, les options de ligne de commande et les variables
  d'environnement propres à l'application de bureau (son éditeur d'environnement local est séparé de
  celui du shell qui lance le script).
- Les **commandes de hooks** (volontairement non lues) : un hook `PreCompact` est signalé, mais le script
  ne peut pas savoir s'il bloque la compaction (il bloque s'il sort avec le code 2 ou renvoie
  `decision: block`).
- L'emplacement de `.claude.json` quand `CLAUDE_CONFIG_DIR` est défini : le script cherche dans ce
  dossier puis dans le dossier personnel. [à vérifier selon votre installation]

## Précision des mesures

- Les tailles en tokens sont une **estimation à environ 4 caractères par token**, pas un décompte du
  tokenizer. `/context` fait foi.
- Les seuils qui déclenchent certains constats (30 skills avec description, 10 serveurs MCP, 60 skills
  après réglage) sont des **seuils indicatifs de cet outil**, pas des seuils officiels.
- Le front-matter YAML des skills et des agents est lu par un analyseur minimal : un cas de YAML
  inhabituel (ancres, valeurs multi-documents) peut être mal lu.

## Péremption

Les réglages, noms de clés, seuils et versions minimales sont ceux de la documentation officielle du
**2026-10-01**. Ils changent d'une version de Claude Code à l'autre : revérifiez les pages citées dans
[BONNES-PRATIQUES.md](BONNES-PRATIQUES.md) au-delà de trois mois, ou avant d'appliquer un réglage
dont la doc a pu évoluer.

## Compromis qualité

Plusieurs leviers sont des compromis, pas des gains gratuits : un plafond de compaction plus bas
résume plus souvent (perte de détail possible), Sonnet pour les sous-agents peut convenir moins bien
à une tâche de raisonnement, `name-only` rend un skill moins facile à déclencher. Chaque levier porte
son risque dans [BONNES-PRATIQUES.md](BONNES-PRATIQUES.md).

## Plateformes

Testé à la main sous Windows 11 avec Python 3.11. Le workflow GitHub Actions du dépôt exécute les tests
sous Linux, macOS et Windows (Python 3.9 et 3.12) : le résultat est dans l'onglet Actions.

Voir aussi : [USAGE.md](USAGE.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
