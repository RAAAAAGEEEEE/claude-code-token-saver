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

## Installer les types d'agents (facultatif)

Les quatre définitions de [../examples/agents/](../examples/agents/) (`executant`, `analyste`, `expert`,
`trieur`) se copient dans `~/.claude/agents/` sans écraser un agent du même nom. Détail et choix :
[BONNES-PRATIQUES.md](BONNES-PRATIQUES.md#choisir-le-sous-agent-le-modèle-et-leffort).

Git Bash, macOS, Linux :

```bash
mkdir -p ~/.claude/agents
for f in ~/.claude/skills/claude-code-token-saver/examples/agents/*.md; do
  [ -e ~/.claude/agents/"$(basename "$f")" ] && echo "existe déjà, ignoré : $(basename "$f")" || cp "$f" ~/.claude/agents/
done
python ~/.claude/skills/claude-code-token-saver/scripts/audit.py --top 0 | grep "Sous-agents"
```

PowerShell :

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\agents" | Out-Null
Get-ChildItem "$HOME\.claude\skills\claude-code-token-saver\examples\agents\*.md" | ForEach-Object {
  $dest = Join-Path "$HOME\.claude\agents" $_.Name
  if (Test-Path $dest) { "existe déjà, ignoré : $($_.Name)" } else { Copy-Item $_.FullName $dest }
}
python "$HOME\.claude\skills\claude-code-token-saver\scripts\audit.py" --top 0 | Select-String "Sous-agents"
```

La dernière ligne doit afficher le nombre de sous-agents personnalisés, dont ceux avec un effort
déclaré. Si `~/.claude/agents/` n'existait pas, redémarrez Claude Code (la documentation demande un
redémarrage après la création du premier fichier d'un nouveau dossier `agents`).

## Mettre à jour

```bash
git -C ~/.claude/skills/claude-code-token-saver pull
```

## Désinstaller

Supprimez le dossier `~/.claude/skills/claude-code-token-saver`. Le skill ne laisse aucun autre
fichier de lui-même ; ce qui reste est ce que vous avez demandé : les rapports `avant.json`, les
sauvegardes `.bak-…` et, si vous les avez installés, les fichiers `executant.md`, `analyste.md`,
`expert.md` et `trieur.md` de `~/.claude/agents/` (à supprimer à la main si vous n'en voulez plus).

Voir aussi : [USAGE.md](USAGE.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
