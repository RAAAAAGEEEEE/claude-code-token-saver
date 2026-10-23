#!/usr/bin/env python3
"""Garde-fou minimal avant d'envoyer du travail à un autre fournisseur.

Exemple générique, bibliothèque standard seulement, aucun accès réseau. Il vérifie ce qui PART :
  1. chaque champ du contenu sortant figure dans une liste blanche ;
  2. aucune valeur ne ressemble à un secret, à une adresse e-mail ou à du code source.

C'est un filet minimal, pas une garantie : adaptez la liste blanche et les motifs à votre cas.

Usage :
    python delestage_garde.py --champs id,texte < envoi.json
Code de sortie : 0 si l'envoi est autorisé, 1 s'il est refusé (la raison va sur la sortie d'erreur,
sans jamais recopier la valeur refusée).
"""

import argparse
import json
import re
import sys
from typing import Iterable, List

SECRET_PATTERNS = [
    ("clé de type sk-", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")),
    ("jeton GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
    ("clé AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("en-tête Bearer", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I)),
    ("clé privée", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("affectation de secret", re.compile(r"\b(api[_-]?key|secret|token|password|mot_de_passe)\s*[:=]\s*\S{6,}", re.I)),
    ("adresse e-mail", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
]

# Lignes qui ressemblent à du code source : heuristique volontairement prudente.
CODE_LINE = re.compile(r"^\s*(def |class |import |from \S+ import |function |const |let |#include|public (static )?\w+ )")


class EnvoiRefuse(Exception):
    pass


def verifier_envoi(contenu: dict, champs_autorises: Iterable[str]) -> None:
    """Lève EnvoiRefuse si le contenu contient un champ non autorisé, un secret ou du code."""
    autorises = set(champs_autorises)
    inconnus = sorted(set(contenu) - autorises)
    if inconnus:
        raise EnvoiRefuse("champs non autorisés : " + ", ".join(inconnus))
    for champ, valeur in contenu.items():
        texte = valeur if isinstance(valeur, str) else json.dumps(valeur, ensure_ascii=False)
        for nom, motif in SECRET_PATTERNS:
            if motif.search(texte):
                raise EnvoiRefuse("champ '%s' : %s détecté(e)" % (champ, nom))
        if any(CODE_LINE.match(ligne) for ligne in texte.splitlines()):
            raise EnvoiRefuse("champ '%s' : ressemble à du code source" % champ)


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--champs", required=True, help="champs autorisés, séparés par des virgules")
    args = parser.parse_args(argv)
    try:
        contenu = json.load(sys.stdin)
        if not isinstance(contenu, dict):
            raise EnvoiRefuse("le contenu doit être un objet JSON")
        verifier_envoi(contenu, [c for c in args.champs.split(",") if c])
    except (EnvoiRefuse, json.JSONDecodeError) as exc:
        print("ENVOI REFUSÉ : %s" % exc, file=sys.stderr)
        return 1
    print("envoi autorisé")
    return 0


if __name__ == "__main__":
    sys.exit(main())
