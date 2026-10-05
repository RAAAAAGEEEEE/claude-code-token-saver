# Changelog

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Versions selon [SemVer](https://semver.org/lang/fr/).

## [1.2.0] - 2026-10-05

### Ajouté
- `scripts/audit.py` (passe en 1.2.0) : option `--depense [--jours N]`, en lecture seule. Elle lit les
  champs `usage` des transcriptions `<config>/projects/*/*.jsonl` et des sous-agents (`subagents/`) et
  affiche le coût estimé en équivalent API par projet, par modèle, pour les sous-agents et par composante
  (entrée, écriture de cache, lecture de cache, sortie). Table de tarifs `PRICES` en constante, datée
  (2026-10-05) et sourcée (page de prix officielle) ; un modèle sans tarif est listé à part, sans coût.
  Documentée dans `docs/USAGE.md`, testée dans `tests/test_depense.py`.
- `docs/BONNES-PRATIQUES.md`, section « Exemple mesuré sur un usage réel : où part l'argent » (mesures de
  l'auteur du 2026-10-05, sur 5 jours, arrondies, étiquetées [rapporté]) : héritage du modèle de la
  session par les sous-agents sans modèle déclaré et ordre de grandeur de son coût ; répartition du coût
  (écriture de cache et sorties d'outils plutôt que contexte fixe en cache) ; condition d'exécution à
  placer dans le script d'un pipeline `claude -p` plutôt que dans le prompt, avec un statut « attente avec
  date » ; poids de départ d'une session de bureau (environ 75 000 tokens) et part réglable ; coût
  d'un relais de messagerie, nul pour les notifications par script.
- Même document : exemple `CLAUDE_CODE_AUTO_COMPACT_WINDOW=300000` (fenêtre effective ramenée au minimum
  des deux valeurs) et « Opus planifie, Sonnet exécute » étiqueté [rapporté, à mesurer].
- `SKILL.md`, `README.md`, `docs/LIMITATIONS.md`, `docs/PRIVACY_AND_SECURITY.md` : mention de `--depense`
  et de ses limites (estimation, pas une facture ; aucun contenu de conversation conservé).

### Modifié
- Dates : documentation officielle toujours vérifiée le 2026-10-01 ; tarifs et mesures du 2026-10-05.

## [1.1.0] - 2026-10-01

### Ajouté
- Choix du bon sous-agent, modèle et effort selon la tâche : section « Choisir le sous-agent, le modèle
  et l'effort » de `docs/BONNES-PRATIQUES.md` (faits vérifiés dans `sub-agents` et `model-config` le
  2026-10-01, table de décision tâche vers agent, règles de conduite, retrait provisoire de Haiku 4.5
  au plus tôt le 2026-10-15, installation) et section correspondante de `SKILL.md`. Le fait que l'outil
  Agent n'ait pas de paramètre d'effort y est présenté comme une déduction (la doc ne décrit qu'un
  paramètre `model`), et le champ `effort` d'un agent comme dominé par `CLAUDE_CODE_EFFORT_LEVEL`.
- `examples/agents/` : quatre définitions génériques `executant` (Sonnet 5.5, `medium`), `analyste`
  (Sonnet 5.5, `high`), `expert` (Opus 5.5, `medium`) et `trieur` (Haiku 4.5 en identifiant complet,
  outils limités à `Read, Grep, Glob`, avec `omitClaudeMd` et `maxTurns`).
- `examples/CLAUDE.md.example` : paragraphe « Choix du sous-agent, du modèle et de l'effort ».
- `scripts/audit.py` (passe en 1.1.0) : métrique `agents_with_effort`, constat `agents-no-effort` (P2)
  quand aucune définition d'agent ne fixe l'effort, et constat `effort-env-overrides-agents` (P2) quand
  `CLAUDE_CODE_EFFORT_LEVEL` est posée alors que des agents fixent leur effort (la variable l'emporte) ;
  la comparaison avant et après suit la nouvelle métrique. `scripts/backup.py` est inchangé (1.0.0).
- `docs/INSTALLATION.md` : installation des types d'agents (bash et PowerShell, sans écraser un agent
  existant) ; la section de désinstallation mentionne les agents copiés.
- Tests : validité des quatre agents d'exemple, effet de leur copie sur l'audit, conflit avec la
  variable d'effort, cohérence du paragraphe `CLAUDE.md`, de la table de décision et des commandes
  d'installation avec les agents fournis.

### Corrigé
- `effortLevel` de premier niveau dans le `settings.json` utilisateur : le constat `effort-heavy`
  l'indique désormais comme sans effet sur Opus 5.5 et les modèles publiés après lui, au lieu de le
  présenter comme un réglage actif ; la documentation précise qu'il s'applique encore à Opus 5, Fable 5.1
  et avant, et à tous les modèles dans les réglages de projet, locaux ou gérés.
- La documentation du modèle des sous-agents précise l'ordre de résolution (depuis la v2.1.251), que
  `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` ne concerne que le champ `model`, et les cas où il faut redémarrer
  pour charger un agent.
- Le test d'absence de tiret cadratin parcourt maintenant aussi les sous-dossiers de `examples/`.

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
