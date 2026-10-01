---
name: claude-code-token-saver
description: >
  Réduit la consommation de tokens et de quota de Claude Code sans perte de qualité : audit en
  lecture seule de la configuration (settings.json, CLAUDE.md, skills, serveurs MCP, sous-agents,
  hooks), rapport priorisé, application avec sauvegarde horodatée et accord de l'utilisateur, mesure
  avant et après. À utiliser quand l'utilisateur dit « économiser des tokens », « audit de
  consommation », « mon quota part vite », « pourquoi ma session coûte autant », « alléger mon
  contexte », ou en anglais « reduce token usage », « Claude Code usage limits », « audit my
  config for cost ». Leviers étiquetés officiel, rapporté ou à vérifier, avec source datée du
  2026-10-01. Ne modifie rien sans accord ; n'affiche jamais de secret.
license: MIT
compatibility: >
  Claude Code (skills personnels ou par projet). Python 3.9+ pour scripts/audit.py et
  scripts/backup.py (bibliothèque standard seulement, aucun accès réseau). Windows, macOS, Linux.
metadata:
  author: Anto1nx
  version: "1.0.0"
  repository: https://github.com/RAAAAAGEEEEE/claude-code-token-saver
allowed-tools: Read Bash(python:*) Bash(python3:*)
---

# claude-code-token-saver

Version 1.0.0, leviers vérifiés dans la documentation officielle le **2026-10-01**
([CHANGELOG.md](CHANGELOG.md)). Au-delà de 3 mois, revérifier les pages citées dans
[docs/BONNES-PRATIQUES.md](docs/BONNES-PRATIQUES.md) : les noms de réglages et les seuils de Claude Code
changent d'une version à l'autre.

Faire dépenser moins de tokens à Claude Code **sans dégrader le résultat** : retirer ce qui est
chargé pour rien, plafonner ce qui grossit sans limite, et le prouver par une mesure avant et après.

## Périmètre

- **Dans** : la configuration de Claude Code de l'utilisateur et du projet courant (`settings.json`,
  `settings.local.json`, `CLAUDE.md`, `.claude/rules/`, skills, sous-agents, hooks, serveurs MCP des
  fichiers) ; les habitudes de session (`/clear`, modèle, effort, sous-agents) ; la mesure avec les
  commandes de Claude Code.
- **Hors** :
  - changer de modèle ou d'effort à la place de l'utilisateur pour « gagner » du quota : c'est un
    choix de qualité, il le fait ;
  - contourner les limites d'un abonnement, ou toucher aux connecteurs claude.ai, aux extensions de
    l'application ou aux comptes (actions manuelles, détaillées dans la doc) ;
  - réécrire le contenu des CLAUDE.md ou des skills sans demande explicite ;
  - toute promesse de gain chiffré : Anthropic ne publie pas la pondération du quota ; seule la
    mesure sur la machine de l'utilisateur fait foi.

## Règles dures

1. **Lecture seule d'abord.** L'audit ne modifie rien. Aucune modification sans accord explicite de
   l'utilisateur dans la conversation, élément par élément ou en bloc.
2. **Sauvegarde horodatée avant toute modification** d'un fichier existant :
   `python "${CLAUDE_SKILL_DIR}/scripts/backup.py" <fichier>` (copie `.bak-AAAA-MM-JJTHH-MM-SS`).
3. **Jamais de secret affiché.** Ni clé, ni jeton, ni contenu du bloc `env`, ni commande de hook, ni
   arguments de serveur MCP, dans une réponse, un rapport ou un fichier produit.
4. **Qualité d'abord.** Chaque levier porte son risque pour la qualité. Un levier qui la dégrade est
   proposé comme compromis, jamais appliqué par défaut (voir « Ce qui est écarté »).
5. **Rien d'inventé.** Un chiffre cité vient de l'audit, d'une page officielle datée ou de la mesure.
   Une affirmation non confirmée est étiquetée **à vérifier**.

## Déroulé

Quatre modes, dans cet ordre. S'arrêter à la fin d'un mode si l'utilisateur ne demande que cela.

### 1. Audit (lecture seule)

```bash
python "${CLAUDE_SKILL_DIR}/scripts/audit.py" --save avant.json
```

Options : `--config-dir`, `--project-dir`, `--json`, `--top N`
([docs/USAGE.md](docs/USAGE.md)). Le script mesure : nombre de skills et taille cumulée de leurs
descriptions (avant et après `skillOverrides`), serveurs MCP des fichiers, présence ou absence de
`autoCompactWindow`, `CLAUDE_CODE_SUBAGENT_MODEL`, niveau d'effort, `skillOverrides`, hooks
`PreCompact`, taille des `CLAUDE.md`, sous-agents sans modèle déclaré. Il ne voit pas les connecteurs
claude.ai, les skills de plugins ni les serveurs intégrés à l'application : les compléter avec
`/context`, `/mcp`, `/doctor` et `/skill-doctor` dans Claude Code.

Si Python est absent : lire les mêmes fichiers à la main avec la grille de
[docs/USAGE.md](docs/USAGE.md#sans-python) et le dire dans le rapport.

### 2. Rapport priorisé

Présenter les constats du script, du plus utile au moins utile, complétés par les mesures de
`/context` et `/usage` quand l'utilisateur les colle. Format :
[exemple de rapport](#exemple-de-rapport). Trois points maximum en tête, en mots simples ; le détail
technique ensuite. Pour chaque constat : ce qui est observé, pourquoi c'est coûteux, l'action, le
risque pour la qualité, l'étiquette de preuve et la source.

### 3. Application (avec accord)

1. Proposer les changements retenus, exactement tels qu'ils seront écrits (clé, valeur, fichier).
2. Attendre l'accord de l'utilisateur.
3. Sauvegarder (règle 2), modifier avec Edit, vérifier que le JSON reste valide :
   `python -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8-sig'))" <fichier>`.
4. Ne jamais toucher au reste du fichier (clés inconnues, permissions, hooks, plugins).
5. Les actions qui ne se font pas dans un fichier (connecteurs, skills de l'application, choix du
   modèle et de l'effort) sont données à l'utilisateur sous forme de tutoriel numéroté
   ([docs/BONNES-PRATIQUES.md](docs/BONNES-PRATIQUES.md#actions-manuelles-dans-lapplication)).

Les réglages s'appliquent aux **nouvelles** sessions ; une session ouverte garde son état.

### 4. Mesure avant et après

1. Avant de changer : `audit.py --save avant.json`, et dans Claude Code `/context` puis `/usage`
   (touche `w` pour les 7 jours).
2. Après : ouvrir une **nouvelle** session, relancer `audit.py --compare avant.json`, puis `/context`
   et `/usage` à nouveau.
3. Rendre les deltas réels, y compris un delta nul. Ne pas conclure d'une seule session : le
   quota dépend de ce qu'on y fait.

## Niveaux de preuve

- **officiel** : page de documentation Anthropic (code.claude.com, platform.claude.com), citée avec
  sa date de consultation.
- **rapporté** : article ou retour d'utilisateur tiers, non mesuré ici.
- **à vérifier** : non confirmé par une source ; à tester avant d'en faire une règle.

Un levier « rapporté » ou « à vérifier » n'est jamais appliqué sans le dire.

## Ce qui est écarté

Aucun levier à gain nul ou à risque de qualité n'est appliqué d'office : baisser les limites de
sortie des commandes (une sortie tronquée peut cacher une erreur), forcer un modèle plus faible sur
tous les sous-agents, désactiver les skills intégrés, couper le cache. Liste complète et raisons :
[docs/BONNES-PRATIQUES.md](docs/BONNES-PRATIQUES.md#ce-qui-est-écarté-et-pourquoi).

## Entrées et sorties

- **Entrée** : une demande ; le dossier de configuration (par défaut `~/.claude`, ou
  `CLAUDE_CONFIG_DIR`) ; le dossier du projet (par défaut le dossier courant) ; éventuellement la
  sortie de `/context` et `/usage` collée par l'utilisateur.
- **Sortie** : un rapport (texte ou JSON), un fichier `avant.json` si demandé, et, après accord, des
  fichiers modifiés avec leur sauvegarde.

## Replis et erreurs

- Dossier de configuration introuvable : `audit.py` sort avec le code 2 ; demander le bon chemin.
- Fichier JSON invalide : l'audit continue, le signale (constat `config-unreadable`) et n'audite pas
  ce fichier ; ne pas le « réparer » sans accord.
- `.claude.json` introuvable : les serveurs MCP des fichiers ne sont pas comptés ; passer par `/mcp`.
- Version de Claude Code antérieure à un réglage cité (exemple : `/skill-doctor` demande
  v2.1.252, `modelSettings` v2.1.251) : donner l'alternative ou dire que la commande manque.

## Exemples d'invocation

- « Mon quota Claude Code part vite, fais un audit. » : modes 1 et 2.
- « Audit de consommation puis applique les changements sûrs. » : modes 1 à 3, avec accord à l'étape 3.
- « J'ai appliqué tes réglages hier, ça a servi à quelque chose ? » : mode 4 avec `--compare`.
- « How do I reduce Claude Code token usage without losing quality? » : mode 2 sur la base de
  [docs/BONNES-PRATIQUES.md](docs/BONNES-PRATIQUES.md), sans audit si l'utilisateur n'en veut pas.

## Exemple de rapport

Illustratif : chiffres fictifs, tirés d'une configuration d'exemple.

```
Trois choses à retenir
1. Vos sessions longues relisent tout le contexte à chaque message : aucun plafond de
   compaction n'est réglé.
2. 58 skills envoient leur description complète à chaque session et à chaque sous-agent (environ
   3 500 tokens de listing, estimation).
3. Les sous-agents prennent le modèle de la session, donc le plus cher.

Détail
[P1] Seuil de compaction non réglé
     Action : /autocompact 400k    Risque qualité : faible (une compaction résume, gardez un fichier de reprise)
     Preuve : officiel, model-config#set-the-auto-compact-window (consulté le 2026-10-01)
[P2] 58 skills sans skillOverrides (listing estimé : environ 3 500 tokens)
     Action : /skill-doctor, puis name-only pour ceux qui servent rarement
     Risque qualité : nul pour les skills conservés, léger pour ceux passés en name-only
...
À mesurer : /context et /usage avant, puis après, dans une nouvelle session.
```

## Procédures PLAN, FIX, VERIFY

- **PLAN** : audit, rapport, liste des changements proposés (clé, valeur, fichier, risque).
- **FIX** : après accord, sauvegarde, modification minimale, validation du JSON.
- **VERIFY** : nouvelle session, `audit.py --compare`, `/context`, `/usage`. Un changement qui ne
  montre aucun effet mesurable est signalé, pas défendu.

## Installation

- Personnelle : `git clone https://github.com/RAAAAAGEEEEE/claude-code-token-saver ~/.claude/skills/claude-code-token-saver`
- Par projet : même commande vers `.claude/skills/claude-code-token-saver` dans le dépôt du projet.
- Python 3.9 ou plus récent pour les scripts, bibliothèque standard seulement.

Détail : [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Sécurité et confidentialité

Rien ne sort de la machine : les scripts lisent des fichiers locaux, n'importent aucun module réseau
et n'impriment aucune valeur de secret. Le rapport peut contenir des noms de skills et de serveurs
MCP : à relire avant de le partager. Détail :
[docs/PRIVACY_AND_SECURITY.md](docs/PRIVACY_AND_SECURITY.md).

## Tests et références

- Tests des scripts : `python -m unittest discover -s tests` (voir [CONTRIBUTING.md](CONTRIBUTING.md)).
- Il n'existe pas d'évaluation automatique du comportement de Claude avec ce skill.
- Sources officielles citées et attributions :
  [docs/LEGAL_AND_ATTRIBUTION.md](docs/LEGAL_AND_ATTRIBUTION.md). Limites :
  [docs/LIMITATIONS.md](docs/LIMITATIONS.md).
