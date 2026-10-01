# Installation

## Prérequis

- Claude Code, terminal ou application de bureau.
- Python 3.9 ou plus récent pour les scripts (`python --version`). Sous macOS et Linux, la commande
  peut s'appeler `python3`.
- Git.

## Installation personnelle (tous vos projets)

```bash
git clone https://github.com/RAAAAAGEEEEE/claude-code-token-saver ~/.claude/skills/claude-code-token-saver
```

Sous Windows, `~` est votre dossier utilisateur (`C:\Users\<vous>`). La commande ci-dessus fonctionne
dans Git Bash ; dans PowerShell :

```powershell
git clone https://github.com/RAAAAAGEEEEE/claude-code-token-saver "$HOME\.claude\skills\claude-code-token-saver"
```

## Installation par projet

```bash
git clone https://github.com/RAAAAAGEEEEE/claude-code-token-saver .claude/skills/claude-code-token-saver
```

à lancer à la racine du dépôt du projet. Retirez ensuite le dossier `.git` du clone si vous voulez
versionner le skill avec le projet.

## Vérifier

```bash
cd ~/.claude/skills/claude-code-token-saver
python -m unittest discover -s tests
python scripts/audit.py --top 3
```

Les tests doivent tous passer, et l'audit affiche un rapport sans rien modifier. Dans Claude Code,
`/skills` doit lister `claude-code-token-saver`.

## Mettre à jour

```bash
git -C ~/.claude/skills/claude-code-token-saver pull
```

## Désinstaller

Supprimez le dossier `~/.claude/skills/claude-code-token-saver`. Le skill ne laisse aucun autre
fichier ; les rapports `avant.json` et les sauvegardes `.bak-…` que vous avez demandés restent où vous
les avez créés.

Voir aussi : [USAGE.md](USAGE.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
