# Dépannage

| Symptôme | Cause probable | Que faire |
|---|---|---|
| `Dossier de configuration introuvable` (code 2) | `~/.claude` n'existe pas, ou `CLAUDE_CONFIG_DIR` pointe ailleurs | Passer `--config-dir <chemin>` avec le dossier qui contient `settings.json`. |
| `python` introuvable | Python absent ou appelé `python3` | Utiliser `python3`, ou installer Python 3.9 ou plus. Sans Python : [USAGE.md](USAGE.md#sans-python). |
| Constat `config-unreadable` : « JSON invalide (ligne N) » | Virgule ou guillemet manquant dans un `settings.json` | Corriger le fichier (ne pas le faire sans sauvegarde) ; Claude Code lui-même ignore un `settings.json` invalide. Relancer l'audit. |
| `Serveurs MCP actifs : 0` alors que vous en utilisez | Les serveurs viennent de connecteurs claude.ai, de l'application ou de plugins : ils ne sont pas dans les fichiers lus | Utiliser `/mcp` et `/context` dans Claude Code. |
| `Skills : 0 trouvés` | Les skills sont ailleurs (plugin, `CLAUDE_CONFIG_DIR` différent) ou le chemin du projet est faux | Vérifier `--config-dir` et `--project-dir`. Les skills de plugins ne sont pas comptés. |
| Le listing estimé diffère de la ligne Skills de `/context` | Le script estime à environ 4 caractères par token et ignore le budget exact du listing | Se fier à `/context` ; le script sert à comparer avant et après. |
| Un réglage modifié « ne marche pas » | La session ouverte garde son état | Ouvrir une nouvelle session. `CLAUDE.md` demande `/clear`, `/compact` ou un redémarrage. |
| `effortLevel` posé dans `settings.json` sans effet sur Opus 5.5 | Clé ignorée au premier niveau du fichier utilisateur sur ce modèle | Voir [CONFIGURATION.md](CONFIGURATION.md#effort--ne-pas-passer-par-effortlevel-sur-opus-55). |
| Un agent copié dans `~/.claude/agents/` n'est pas proposé | Le dossier `agents` n'existait pas au lancement de la session (la doc demande un redémarrage après le premier fichier), ou le front-matter est mal formé | Redémarrer Claude Code ; vérifier le front-matter ; `audit.py` doit compter l'agent (ligne « Sous-agents personnalisés »). |
| `/skill-doctor` introuvable | Claude Code antérieur à v2.1.252, ou récupération des drapeaux de fonctionnalités désactivée | Mettre à jour Claude Code ; sinon `/skills` (touche `t` pour trier par taille). |
| Caractères mal affichés sous Windows | Console en codage ancien | Le script force l'UTF-8 ; sinon `chcp 65001` ou `PYTHONIOENCODING=utf-8`. |
| `Comparaison impossible` | Fichier `--compare` absent ou non écrit par `--save` | Refaire `--save avant.json` avant de modifier. |
| Les tests sont lents sous Windows | Chaque test de ligne de commande démarre un interpréteur Python, et l'antivirus peut le ralentir | Normal : de quelques secondes à une minute selon la machine. |

Un problème qui n'est pas dans ce tableau : ouvrez une issue sans joindre de rapport contenant des
noms de serveurs ou de skills que vous ne voulez pas publier.

Voir aussi : [LIMITATIONS.md](LIMITATIONS.md), [USAGE.md](USAGE.md).
