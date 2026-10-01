#!/usr/bin/env python3
"""Copie horodatée (ISO 8601) d'un ou plusieurs fichiers de configuration, avant modification.

Bibliothèque standard uniquement (Python 3.9+), Windows, macOS et Linux.
Ne modifie jamais le fichier d'origine et n'écrase jamais une sauvegarde existante.
La copie est créée à côté de l'original : <fichier>.bak-AAAA-MM-JJTHH-MM-SS
(tirets à la place des deux-points, interdits dans les noms de fichiers Windows).

Usage : python backup.py FICHIER [FICHIER ...]
Code de sortie : 0 si toutes les copies sont faites, 1 si au moins une a échoué.
"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

VERSION = "1.0.0"


def backup_path(source: Path, now: datetime | None = None) -> Path:
    stamp = (now or datetime.now()).strftime("%Y-%m-%dT%H-%M-%S")
    return source.with_name(f"{source.name}.bak-{stamp}")


def backup(source: Path, now: datetime | None = None) -> Path:
    if not source.is_file():
        raise FileNotFoundError(f"fichier absent : {source}")
    target = backup_path(source, now)
    if target.exists():
        raise FileExistsError(f"la sauvegarde existe déjà : {target}")
    shutil.copy2(source, target)
    return target


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 1
    if args[0] == "--version":
        print(f"backup.py {VERSION}")
        return 0
    failed = False
    for name in args:
        try:
            print(backup(Path(name).expanduser()))
        except (OSError, ValueError) as exc:
            print(f"ÉCHEC {name} : {exc}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
