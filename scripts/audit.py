#!/usr/bin/env python3
"""Audit en lecture seule de la configuration Claude Code, côté consommation de tokens.

Bibliothèque standard uniquement (Python 3.9+), Windows, macOS et Linux.
Aucun accès réseau. Aucune écriture, sauf --save (fichier JSON de mesures
que vous désignez). Aucune valeur de secret n'est lue pour être affichée :
le script n'imprime que des noms, des nombres et des états.

Usage : python audit.py [--config-dir DIR] [--project-dir DIR] [--json]
                        [--save FICHIER] [--compare FICHIER] [--top N]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION = "1.3.0"
DOCS_DATE = "2026-10-01"
CHARS_PER_TOKEN = 4  # estimation grossière, étiquetée comme telle dans la sortie
DEFAULT_DESC_CAP = 1536  # doc skills : plafond description + when_to_use dans le listing
EXIT_OK = 0
EXIT_NO_CONFIG = 2

# Variables d'environnement lues (jamais d'autres valeurs). Le contenu du bloc
# "env" de settings.json n'est pas affiché hors de cette liste blanche.
WATCHED_ENV = (
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW",
    "CLAUDE_CODE_SUBAGENT_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL_FORCE",
    "CLAUDE_CODE_EFFORT_LEVEL",
    "ENABLE_TOOL_SEARCH",
    "CLAUDE_CODE_DISABLE_1M_CONTEXT",
    "DISABLE_PROMPT_CACHING",
    "DISABLE_PROMPT_CACHING_HAIKU",
    "DISABLE_PROMPT_CACHING_SONNET",
    "DISABLE_PROMPT_CACHING_OPUS",
    "DISABLE_PROMPT_CACHING_FABLE",
    "FORCE_PROMPT_CACHING_5M",
    "SLASH_COMMAND_TOOL_CHAR_BUDGET",
)
BROWSER_WORDS = ("browser", "chrome", "playwright", "puppeteer", "devtools")
HEAVY_EFFORTS = ("high", "xhigh", "max")
PRIORITY_ORDER = {"P1": 0, "P2": 1, "P3": 2}


# --------------------------------------------------------------------------
# Lecture de fichiers
# --------------------------------------------------------------------------

def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def read_json(path: Path) -> tuple[dict | None, str | None]:
    """Retourne (données, erreur). Fichier absent : (None, None)."""
    if not path.is_file():
        return None, None
    text = read_text(path)
    if text is None:
        return None, "illisible"
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"JSON invalide (ligne {exc.lineno})"
    if not isinstance(data, dict):
        return None, "JSON inattendu (objet attendu)"
    return data, None


def short(path: Path | str) -> str:
    """Remplace le dossier personnel par ~ pour ne pas afficher de nom d'utilisateur."""
    text = str(path)
    home = str(Path.home())
    if text.startswith(home):
        text = "~" + text[len(home):]
    return text.replace("\\", "/")


_FOLD_MARKERS = {">", "|", ">-", "|-", ">+", "|+"}
_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")


def parse_frontmatter(text: str) -> dict[str, str]:
    """Front-matter YAML minimal : clés de premier niveau, valeurs scalaires ou repliées."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    block: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        block.append(line)
    else:
        return {}
    result: dict[str, str] = {}
    i = 0
    while i < len(block):
        match = _KEY_RE.match(block[i])
        if not match:
            i += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        i += 1
        if value in _FOLD_MARKERS or value == "":
            parts = []
            while i < len(block) and (block[i].startswith((" ", "\t")) or not block[i].strip()):
                parts.append(block[i].strip())
                i += 1
            value = " ".join(p for p in parts if p)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        result[key] = value
    return result


# --------------------------------------------------------------------------
# Collecte
# --------------------------------------------------------------------------

def collect_settings(config_dir: Path, project_dir: Path) -> dict:
    files = [
        ("local", project_dir / ".claude" / "settings.local.json"),
        ("project", project_dir / ".claude" / "settings.json"),
        ("user", config_dir / "settings.json"),
    ]
    layers, errors = [], []
    for scope, path in files:
        data, err = read_json(path)
        if err:
            errors.append(f"{scope} ({short(path)}) : {err}")
        if data is not None:
            layers.append((scope, data))
    return {"layers": layers, "errors": errors}


def setting(settings: dict, key: str):
    """Première valeur trouvée par ordre de priorité local > project > user."""
    for scope, data in settings["layers"]:
        if key in data:
            return data[key], scope
    return None, None


def env_value(settings: dict, name: str):
    """Valeur d'une variable surveillée.

    Le bloc env de settings.json prime sur le shell dans la plupart des sessions
    (doc env-vars#precedence) ; à défaut, on regarde l'environnement du shell qui
    lance ce script, qui peut différer de celui de Claude Code.
    """
    for scope, data in settings["layers"]:
        env = data.get("env")
        if isinstance(env, dict) and name in env and env[name] not in (None, ""):
            return str(env[name]), scope
    if os.environ.get(name) not in (None, ""):
        return os.environ[name], "environnement"
    return None, None


def collect_skills(config_dir: Path, project_dir: Path, overrides: dict, cap: int) -> list[dict]:
    roots = [
        ("user", config_dir / "skills"),
        ("project", project_dir / ".claude" / "skills"),
    ]
    skills: list[dict] = []
    for scope, root in roots:
        if not root.is_dir():
            continue
        candidates = []
        for child in sorted(root.iterdir()):
            if child.name.startswith("."):
                continue
            if child.name.lower() == "synced" and child.is_dir():
                candidates += [("synced", sub) for sub in sorted(child.iterdir())]
            else:
                candidates.append((scope, child))
        for kind, folder in candidates:
            skill_file = folder / "SKILL.md"
            if not skill_file.is_file():
                continue
            text = read_text(skill_file) or ""
            meta = parse_frontmatter(text)
            name = meta.get("name") or folder.name
            desc = meta.get("description", "")
            when = meta.get("when_to_use", "")
            combined = len(desc) + len(when)
            model_invocable = meta.get("disable-model-invocation", "").lower() != "true"
            state = overrides.get(name, "on") if isinstance(overrides, dict) else "on"
            if not model_invocable or state in ("off", "user-invocable-only"):
                listed = 0
            elif state == "name-only":
                listed = len(name)
            else:
                listed = len(name) + min(combined, cap)
            skills.append({
                "name": name,
                "scope": kind,
                "desc_chars": combined,
                "listed_chars": listed,
                "state": state,
                "model_invocable": model_invocable,
                "truncated": combined > cap,
            })
    return skills


def project_key_matches(key: str, project_dir: Path) -> bool:
    def norm(value: str) -> str:
        return value.replace("\\", "/").rstrip("/").lower()
    return norm(key) == norm(str(project_dir))


def collect_mcp(config_dir: Path, project_dir: Path) -> dict:
    names: dict[str, str] = {}
    disabled: set[str] = set()
    errors: list[str] = []
    state_candidates = [config_dir / ".claude.json", Path.home() / ".claude.json"]
    state_path = next((p for p in state_candidates if p.is_file()), None)
    if state_path is not None:
        data, err = read_json(state_path)
        if err:
            errors.append(f"{short(state_path)} : {err}")
        if data:
            servers = data.get("mcpServers")
            if isinstance(servers, dict):
                for name in servers:
                    names[name] = "user"
            projects = data.get("projects")
            if isinstance(projects, dict):
                for key, entry in projects.items():
                    if isinstance(entry, dict) and project_key_matches(key, project_dir):
                        local = entry.get("mcpServers")
                        if isinstance(local, dict):
                            for name in local:
                                names.setdefault(name, "local")
                        off = entry.get("disabledMcpServers")
                        if isinstance(off, list):
                            disabled.update(str(x) for x in off)
    mcp_json, err = read_json(project_dir / ".mcp.json")
    if err:
        errors.append(f".mcp.json : {err}")
    if mcp_json and isinstance(mcp_json.get("mcpServers"), dict):
        for name in mcp_json["mcpServers"]:
            names.setdefault(name, "project")
    active = {n: s for n, s in names.items() if n not in disabled}
    return {
        "configured": sorted(names),
        "disabled": sorted(n for n in names if n in disabled),
        "active": sorted(active),
        "state_file_found": state_path is not None,
        "errors": errors,
    }


def collect_memory_files(config_dir: Path, project_dir: Path) -> list[dict]:
    candidates = [
        ("user", config_dir / "CLAUDE.md"),
        ("project", project_dir / "CLAUDE.md"),
        ("project", project_dir / ".claude" / "CLAUDE.md"),
        ("local", project_dir / "CLAUDE.local.md"),
    ]
    files = []
    for scope, path in candidates:
        text = read_text(path) if path.is_file() else None
        if text is None:
            continue
        lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        imports = len(re.findall(r"(?m)^[^\n`]*(?<![\w@])@[\w./~-]+\.\w+", text))
        files.append({
            "scope": scope,
            "path": short(path),
            "lines": lines,
            "chars": len(text),
            "imports": imports,
        })
    return files


def collect_rules(config_dir: Path, project_dir: Path) -> dict:
    total = unconditional = 0
    for root in (config_dir / "rules", project_dir / ".claude" / "rules"):
        if not root.is_dir():
            continue
        for path in root.rglob("*.md"):
            total += 1
            meta = parse_frontmatter(read_text(path) or "")
            if "paths" not in meta:
                unconditional += 1
    return {"total": total, "unconditional": unconditional}


def collect_agents(config_dir: Path, project_dir: Path) -> dict:
    total = without_model = with_effort = 0
    for root in (config_dir / "agents", project_dir / ".claude" / "agents"):
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.md")):
            total += 1
            meta = parse_frontmatter(read_text(path) or "")
            if not meta.get("model"):
                without_model += 1
            if meta.get("effort"):
                with_effort += 1
    return {"total": total, "without_model": without_model, "with_effort": with_effort}


def collect_hooks(settings: dict) -> dict:
    """Événements de hooks présents (jamais les commandes)."""
    events: dict[str, int] = {}
    for _scope, data in settings["layers"]:
        hooks = data.get("hooks")
        if not isinstance(hooks, dict):
            continue
        for event, entries in hooks.items():
            count = 0
            if isinstance(entries, list):
                for entry in entries:
                    inner = entry.get("hooks") if isinstance(entry, dict) else None
                    count += len(inner) if isinstance(inner, list) else 1
            events[event] = events.get(event, 0) + count
    return events


# --------------------------------------------------------------------------
# Analyse
# --------------------------------------------------------------------------

# Tarifs API en USD par million de tokens : (entrée, écriture cache 5 min, écriture cache 1 h,
# lecture cache, sortie). Source : https://platform.claude.com/docs/en/about-claude/pricing,
# consultée le 2026-10-05. Constante à revérifier : les prix changent. Un modèle absent de la table
# est compté à part, sans coût (jamais de prix inventé). Clés : identifiant sans suffixe de date.
PRICES_DATE = "2026-10-05"
PRICES_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"
PRICES = {
    "claude-fable-5-1": (10.0, 12.5, 20.0, 0.25, 50.0),
    "claude-fable-5": (10.0, 12.5, 20.0, 1.0, 50.0),
    "claude-opus-5-5": (4.0, 5.0, 8.0, 0.20, 20.0),
    "claude-opus-5": (5.0, 6.25, 10.0, 0.50, 25.0),
    "claude-opus-4-8": (5.0, 6.25, 10.0, 0.50, 25.0),
    "claude-opus-4-7": (5.0, 6.25, 10.0, 0.50, 25.0),
    "claude-opus-4-6": (5.0, 6.25, 10.0, 0.50, 25.0),
    "claude-opus-4-5": (5.0, 6.25, 10.0, 0.50, 25.0),
    "claude-opus-4-1": (15.0, 18.75, 30.0, 1.50, 75.0),
    "claude-opus-4": (15.0, 18.75, 30.0, 1.50, 75.0),
    "claude-sonnet-5-5": (2.0, 2.5, 4.0, 0.20, 10.0),
    "claude-sonnet-5": (2.0, 2.5, 4.0, 0.20, 10.0),
    "claude-sonnet-4-6": (3.0, 3.75, 6.0, 0.30, 15.0),
    "claude-sonnet-4-5": (3.0, 3.75, 6.0, 0.30, 15.0),
    "claude-sonnet-4": (3.0, 3.75, 6.0, 0.30, 15.0),
    "claude-haiku-4-5": (1.0, 1.25, 2.0, 0.10, 5.0),
    "claude-haiku-3-5": (0.80, 1.0, 1.60, 0.08, 4.0),
}


def price_key(model: str) -> str | None:
    """Clé de PRICES pour un identifiant de modèle (suffixe de date et [1m] ignorés), sinon None."""
    name = re.sub(r"\[.*?\]$", "", model or "").strip().lower()
    name = re.sub(r"-\d{8}$", "", name)
    return name if name in PRICES else None


def cache_write_split(usage: dict) -> tuple[int, int]:
    """(tokens écrits en cache 5 min, tokens écrits en cache 1 h) d'un bloc `usage`."""
    created = usage.get("cache_creation_input_tokens") or 0
    detail = usage.get("cache_creation") or {}
    w1 = detail.get("ephemeral_1h_input_tokens") or 0
    w5 = detail.get("ephemeral_5m_input_tokens")
    if w5 is None:
        w5 = max(created - w1, 0)
    return w5, w1


def usage_parts(model: str, usage: dict) -> dict | None:
    """Coût estimé en USD par composante d'un bloc `usage`, ou None si le modèle n'a pas de tarif."""
    key = price_key(model)
    if key is None:
        return None
    p_in, p_w5, p_w1, p_read, p_out = PRICES[key]
    w5, w1 = cache_write_split(usage)
    return {
        "input": (usage.get("input_tokens") or 0) * p_in / 1e6,
        "cache_write": (w5 * p_w5 + w1 * p_w1) / 1e6,
        "cache_read": (usage.get("cache_read_input_tokens") or 0) * p_read / 1e6,
        "output": (usage.get("output_tokens") or 0) * p_out / 1e6,
    }


def usage_cost(model: str, usage: dict) -> float | None:
    """Coût estimé en USD d'un bloc `usage`, ou None si le modèle n'a pas de tarif."""
    parts = usage_parts(model, usage)
    return None if parts is None else sum(parts.values())


def project_label(dirname: str) -> str:
    """Nom lisible d'un dossier de projet (deux derniers segments du chemin encodé)."""
    parts = [x for x in re.split(r"-+", dirname) if x]
    return "-".join(parts[-2:]) if len(parts) > 1 else (dirname or "?")


def collect_spend(projects_dir: Path, days: int, now: datetime | None = None) -> dict:
    """Lit en lecture seule les transcriptions `*/*.jsonl` et `*/*/subagents/*.jsonl`.

    Chaque message est compté une fois (identifiant de message ; quand il est écrit en plusieurs
    blocs, le bloc au plus grand output_tokens est gardé). Seuls les champs `usage`, `model`,
    `timestamp` et l'identifiant sont lus : aucun contenu de conversation n'est conservé.
    """
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    seen: dict[str, tuple] = {}
    files = 0
    if projects_dir.is_dir():
        for path in projects_dir.rglob("*.jsonl"):
            rel = path.relative_to(projects_dir).parts
            project = rel[0]
            sub = "subagents" in rel[:-1]
            files += 1
            try:
                handle = open(path, encoding="utf-8", errors="replace")
            except OSError:
                continue
            with handle:
                for line in handle:
                    if '"usage"' not in line:
                        continue
                    try:
                        obj = json.loads(line)
                    except ValueError:
                        continue
                    msg = obj.get("message") if isinstance(obj, dict) else None
                    if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
                        continue
                    try:
                        when = datetime.fromisoformat(str(obj.get("timestamp")).replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    if when.tzinfo is None:
                        when = when.replace(tzinfo=timezone.utc)
                    if when < since:
                        continue
                    model = msg.get("model") or "?"
                    if model == "<synthetic>":
                        continue
                    ident = msg.get("id") or obj.get("uuid") or f"{path}:{when.isoformat()}"
                    old = seen.get(ident)
                    out_new = msg["usage"].get("output_tokens") or 0
                    if old is None or out_new >= (old[3].get("output_tokens") or 0):
                        seen[ident] = (project, sub, model, msg["usage"])
    by_project: dict[str, float] = {}
    by_model: dict[str, float] = {}
    sub_by_model: dict[str, float] = {}
    components = {"input": 0.0, "cache_write": 0.0, "cache_read": 0.0, "output": 0.0}
    unpriced: dict[str, int] = {}
    total = sub_total = 0.0
    for project, sub, model, usage in seen.values():
        parts = usage_parts(model, usage)
        if parts is None:
            unpriced[model] = unpriced.get(model, 0) + 1
            continue
        cost = sum(parts.values())
        key = price_key(model)
        label = project_label(project)
        by_project[label] = by_project.get(label, 0.0) + cost
        by_model[key] = by_model.get(key, 0.0) + cost
        total += cost
        if sub:
            sub_total += cost
            sub_by_model[key] = sub_by_model.get(key, 0.0) + cost
        for name, value in parts.items():
            components[name] += value
    return {"days": days, "files": files, "messages": len(seen), "total": total,
            "subagents_total": sub_total, "by_project": by_project, "by_model": by_model,
            "subagents_by_model": sub_by_model, "by_component": components, "unpriced": unpriced}


def render_spend(spend: dict, top: int = 10) -> str:
    def rows(data: dict, limit: int | None = None) -> list[str]:
        items = sorted(data.items(), key=lambda kv: -kv[1])
        return [f"  {name:<40} {value:>10.2f} $" for name, value in (items[:limit] if limit else items)]

    out = [f"Dépense estimée sur {spend['days']} jours, en équivalent API "
           f"(tarifs du {PRICES_DATE}, {PRICES_SOURCE})",
           f"Total : {spend['total']:.2f} $ ({spend['messages']} messages, {spend['files']} transcriptions)"]
    share = f" ({100 * spend['subagents_total'] / spend['total']:.0f} % du total)" if spend["total"] else ""
    out.append(f"Dont sous-agents : {spend['subagents_total']:.2f} ${share}")
    out.append("")
    out.append("Par projet")
    out += rows(spend["by_project"], top) or ["  aucun"]
    out.append("Par modèle")
    out += rows(spend["by_model"]) or ["  aucun"]
    out.append("Sous-agents, par modèle")
    out += rows(spend["subagents_by_model"]) or ["  aucun"]
    out.append("Par composante")
    out += rows(spend["by_component"])
    if spend["unpriced"]:
        out.append("Modèles sans tarif dans la table (non comptés) : "
                   + ", ".join(f"{m} ({n} messages)" for m, n in sorted(spend["unpriced"].items())))
    out.append("")
    out.append("Estimation : équivalent API, pas la facture d'un abonnement ni sa pondération de quota. "
               "Lecture seule, aucun contenu de conversation n'est affiché.")
    return "\n".join(out)


def est_tokens(chars: int) -> int:
    return round(chars / CHARS_PER_TOKEN)


def finding(priority: str, fid: str, title: str, why: str, fix: str, source: str) -> dict:
    return {"priority": priority, "id": fid, "title": title, "why": why, "fix": fix, "source": source}


def analyse(config_dir: Path, project_dir: Path) -> dict:
    settings = collect_settings(config_dir, project_dir)
    overrides_raw, _ = setting(settings, "skillOverrides")
    overrides = overrides_raw if isinstance(overrides_raw, dict) else {}
    cap_raw, _ = setting(settings, "skillListingMaxDescChars")
    cap = cap_raw if isinstance(cap_raw, int) and cap_raw > 0 else DEFAULT_DESC_CAP

    skills = collect_skills(config_dir, project_dir, overrides, cap)
    mcp = collect_mcp(config_dir, project_dir)
    memory = collect_memory_files(config_dir, project_dir)
    rules = collect_rules(config_dir, project_dir)
    agents = collect_agents(config_dir, project_dir)
    hooks = collect_hooks(settings)
    env = {name: env_value(settings, name) for name in WATCHED_ENV}

    override_states = {"name-only": 0, "user-invocable-only": 0, "off": 0}
    for state in overrides.values():
        if state in override_states:
            override_states[state] += 1

    listed_chars = sum(s["listed_chars"] for s in skills)
    full_chars = sum(len(s["name"]) + min(s["desc_chars"], cap) for s in skills)
    visible = [s for s in skills if s["listed_chars"] > 0]
    with_desc = [s for s in skills if s["listed_chars"] > len(s["name"])]
    memory_chars = sum(f["chars"] for f in memory)

    window_env = env["CLAUDE_CODE_AUTO_COMPACT_WINDOW"]
    window_set, window_scope = setting(settings, "autoCompactWindow")
    window_value = None
    if window_env[0] is not None:
        window_value = window_env[0]
    elif window_set is not None:
        window_value = window_set

    metrics = {
        "skills_total": len(skills),
        "skills_visible": len(visible),
        "skills_with_description": len(with_desc),
        "skills_listing_est_tokens": est_tokens(listed_chars),
        "skills_listing_without_overrides_est_tokens": est_tokens(full_chars),
        "mcp_servers_active": len(mcp["active"]),
        "mcp_servers_configured": len(mcp["configured"]),
        "memory_files": len(memory),
        "memory_est_tokens": est_tokens(memory_chars),
        "memory_max_lines": max((f["lines"] for f in memory), default=0),
        "agents_total": agents["total"],
        "agents_without_model": agents["without_model"],
        "agents_with_effort": agents["with_effort"],
        "rules_unconditional": rules["unconditional"],
        "autocompact_window": window_value,
        "precompact_hooks": hooks.get("PreCompact", 0),
    }

    findings: list[dict] = []

    # 1. Seuil de compaction
    if window_value is None:
        findings.append(finding(
            "P1", "compact-window",
            "Seuil de compaction automatique non réglé",
            "Sans réglage, la compaction se déclenche près de la limite de la fenêtre du modèle "
            "(environ 967 000 tokens pour les modèles à fenêtre de 1 million). Chaque requête "
            "relit tout le contexte : une session très longue coûte de plus en plus cher par message.",
            "Dans une session : /autocompact 400k (valeur d'exemple, entre 100k et 1M). "
            "Ou dans settings.json : \"autoCompactWindow\": 400000. Une compaction résume : "
            "gardez un fichier de reprise pour les travaux longs.",
            "model-config#set-the-auto-compact-window, settings-reference#autocompactwindow",
        ))
    # 2. Hook PreCompact
    if hooks.get("PreCompact"):
        findings.append(finding(
            "P1", "precompact-hook",
            "Un hook PreCompact est configuré",
            "Un hook PreCompact qui sort avec le code 2 ou renvoie \"decision\": \"block\" empêche la "
            "compaction ; si c'est la compaction automatique, le contexte grossit jusqu'à la limite "
            "du modèle, puis la requête échoue. "
            "Le script ne peut pas être jugé ici (ses commandes ne sont pas lues).",
            "Relire le script du hook. S'il sert à sauvegarder avant compaction, le faire sortir "
            "avec le code 0 ; un hook PostCompact tourne après coup (utile pour exporter le "
            "résumé) et ne peut pas bloquer.",
            "hooks#precompact",
        ))
    # 3. Recherche d'outils MCP
    tool_search, ts_scope = env["ENABLE_TOOL_SEARCH"]
    if tool_search is not None and tool_search.strip().lower() in ("false", "0"):
        findings.append(finding(
            "P1", "tool-search-off",
            "La recherche d'outils MCP est désactivée",
            "Par défaut, les définitions d'outils MCP ne sont pas chargées d'avance : seuls les noms "
            "et instructions des serveurs le sont. Désactivée, chaque outil de chaque serveur est "
            "chargé à chaque session.",
            "Retirer ENABLE_TOOL_SEARCH=false (ou le passer à true), sauf passerelle qui ne la gère pas.",
            "mcp#scale-with-mcp-tool-search",
        ))
    # 4. Cache de prompt désactivé
    disabled_cache = [n for n in WATCHED_ENV if n.startswith("DISABLE_PROMPT_CACHING")
                      and env[n][0] not in (None, "", "0")]
    if disabled_cache:
        findings.append(finding(
            "P1", "prompt-cache-off",
            "Le cache de prompt est désactivé (" + ", ".join(disabled_cache) + ")",
            "Sans cache, chaque requête retraite tout le contexte au tarif plein.",
            "Retirer la variable, sauf pour un diagnostic ponctuel.",
            "prompt-caching#disable-prompt-caching",
        ))
    # 5. Sous-agents
    sub_model, _ = env["CLAUDE_CODE_SUBAGENT_MODEL"]
    sub_force, _ = env["CLAUDE_CODE_SUBAGENT_MODEL_FORCE"]
    if sub_model is None:
        extra = ""
        if agents["total"]:
            extra = (f" Vos {agents['total']} sous-agents personnalisés comptent "
                     f"{agents['without_model']} sans champ `model`.")
        findings.append(finding(
            "P2", "subagent-model",
            "Aucun modèle par défaut pour les sous-agents",
            "Un sous-agent sans modèle déclaré hérite du modèle de la session. Si la session tourne "
            "sur le modèle le plus cher, chaque sous-agent aussi. (Explore et Plan ne suivent pas "
            "cette variable sans _FORCE : ils héritent de la session, plafonnés à Opus.)" + extra,
            "Si la qualité le permet pour vos tâches : CLAUDE_CODE_SUBAGENT_MODEL=sonnet dans le "
            "bloc env de settings.json, sans _FORCE (Claude peut alors encore demander un autre "
            "modèle pour un appel précis). Les sous-agents qui déclarent leur propre modèle ne "
            "changent pas.",
            "sub-agents#choose-a-model, env-vars",
        ))
    if sub_force not in (None, "", "0"):
        findings.append(finding(
            "P3", "subagent-force",
            "CLAUDE_CODE_SUBAGENT_MODEL_FORCE est actif",
            "Un seul modèle est imposé à tous les sous-agents, y compris à ceux qui déclarent le leur "
            "(contre-revue sur un modèle plus fort, par exemple).",
            "Vérifier que c'est voulu pour la qualité des revues.",
            "sub-agents#run-every-subagent-on-one-model",
        ))
    # 6. Effort
    heavy_sources = []
    env_effort, _ = env["CLAUDE_CODE_EFFORT_LEVEL"]
    if env_effort and env_effort.lower() in HEAVY_EFFORTS:
        heavy_sources.append(f"CLAUDE_CODE_EFFORT_LEVEL={env_effort.lower()}")
    top_effort, top_scope = setting(settings, "effortLevel")
    if isinstance(top_effort, str) and top_effort.lower() in HEAVY_EFFORTS:
        note = " : sans effet sur Opus 5.5 et suivants" if top_scope == "user" else ""
        heavy_sources.append(f"effortLevel={top_effort.lower()} ({top_scope}{note})")
    model_settings, _ = setting(settings, "modelSettings")
    if isinstance(model_settings, dict):
        for model, entry in model_settings.items():
            lvl = entry.get("effortLevel") if isinstance(entry, dict) else None
            if isinstance(lvl, str) and lvl.lower() in HEAVY_EFFORTS:
                heavy_sources.append(f"modelSettings.{model}={lvl.lower()}")
    if heavy_sources:
        findings.append(finding(
            "P2", "effort-heavy",
            "Niveau d'effort élevé par défaut (" + "; ".join(heavy_sources) + ")",
            "Les niveaux élevés raisonnent plus longtemps : plus de tokens de sortie. Opus 5.5 et "
            "Sonnet 5.5 démarrent en medium, qui suffit pour la plupart des tâches courantes.",
            "Choisir l'effort par session avec /effort (ou le sélecteur de modèle), et réserver "
            "high ou xhigh aux tâches difficiles, ou fixer l'effort par type de sous-agent (champ "
            "effort, sans CLAUDE_CODE_EFFORT_LEVEL posée : elle l'emporte). Sur Opus 5.5, Sonnet 5.5 et Fable 5.1, changer d'effort ne casse pas le cache "
            "(abonnement ou clé API ; conditions dans la doc).",
            "model-config#adjust-effort-level",
        ))
    user_effort = dict(settings["layers"]).get("user", {}).get("effortLevel")
    if user_effort is not None:
        findings.append(finding(
            "P3", "effort-toplevel-ignored",
            "effortLevel dans le settings.json utilisateur : sans effet sur Opus 5.5 et les modèles suivants",
            "La documentation indique que cette clé (ancienne forme) ne compte pas pour Opus 5.5 ; "
            "elle s'applique encore à Opus 5, à Fable 5.1 et aux modèles antérieurs.",
            "Pour Opus 5.5 : /effort ou le sélecteur de modèle (écrit modelSettings), ou la variable "
            "CLAUDE_CODE_EFFORT_LEVEL. Pour un sous-agent : champ effort de sa définition.",
            "model-config#adjust-effort-level",
        ))
    # 6 bis. Définitions d'agents avec effort
    if agents["with_effort"] == 0:
        if agents["total"]:
            title = (f"Aucun de vos {agents['total']} sous-agents personnalisés ne fixe son effort")
        else:
            title = "Aucun sous-agent personnalisé : modèle et effort ne se règlent pas par tâche"
        findings.append(finding(
            "P2", "agents-no-effort", title,
            "La documentation ne décrit qu'un paramètre model à l'appel de l'outil Agent, pas "
            "d'effort : l'effort d'un sous-agent vient de sa définition (champ effort) ou, à "
            "défaut, de la session. Sans définition, une tâche simple tourne au niveau d'effort de "
            "la session, et une tâche d'analyse ne peut pas être montée en effort sans changer "
            "toute la session.",
            "Copier les quatre définitions de examples/agents/ du skill (executant, analyste, expert, "
            "trieur) dans ~/.claude/agents/, ou écrire les vôtres avec model et effort. Une "
            "définition est un fichier : elle ne change rien tant qu'un agent n'est pas appelé.",
            "sub-agents#supported-frontmatter-fields, sub-agents#choose-a-model, model-config#set-the-effort-level",
        ))
    if agents["with_effort"] and env_effort and env_effort.strip().lower() != "auto":
        findings.append(finding(
            "P2", "effort-env-overrides-agents",
            f"CLAUDE_CODE_EFFORT_LEVEL est posée alors que {agents['with_effort']} agent(s) fixent leur effort",
            "Le champ effort d'un sous-agent remplace l'effort de la session, mais pas la variable "
            "CLAUDE_CODE_EFFORT_LEVEL : tant qu'elle est posée, tous les agents tournent à son niveau. "
            "(Un plafond maxEffortLevel ou d'organisation limite les deux ; il n'est pas lisible ici.)",
            "Retirer la variable (et choisir l'effort de la session avec /effort), ou renoncer à "
            "l'effort par type d'agent.",
            "model-config#set-the-effort-level",
        ))
    # 7. Workflows automatiques
    ultracode, _ = setting(settings, "ultracode")
    if ultracode is True:
        findings.append(finding(
            "P2", "ultracode",
            "ultracode est activé",
            "Claude prévoit un workflow pour chaque tâche substantielle, sans qu'on le demande : "
            "chaque agent du workflow envoie ses propres requêtes.",
            "Le laisser à false par défaut et l'activer par session quand une tâche le justifie.",
            "settings-reference#ultracode, costs#why-usage-climbs-in-a-long-session",
        ))
    # 8. Skills
    if len(visible) and not any(override_states.values()) and len(with_desc) >= 30:
        saving = est_tokens(listed_chars)
        findings.append(finding(
            "P2", "skills-many",
            f"{len(with_desc)} skills avec description complète et aucun skillOverrides",
            f"Chaque skill visible ajoute son nom et sa description au contexte de chaque session et de "
            f"chaque sous-agent (listing estimé : environ {saving} tokens, estimation à "
            f"{CHARS_PER_TOKEN} caractères par token). Au-delà du budget du listing "
            f"(1 % de la fenêtre), les descriptions des skills les moins utilisés sautent en premier.",
            "Lancer /skill-doctor (skills jamais utilisés), puis dans /skills mettre les skills "
            "rarement utiles en name-only (Claude les voit par leur nom) ou user-only (vous seul les "
            "appelez avec /nom). Les descriptions des skills utilisés restent intactes.",
            "skills#override-skill-visibility-from-settings, skills#find-unused-skills",
        ))
    elif len(with_desc) >= 60:
        findings.append(finding(
            "P3", "skills-still-many",
            f"{len(with_desc)} skills restent listés avec leur description",
            "Le listing reste volumineux malgré vos skillOverrides.",
            "Relancer /skill-doctor et réduire encore.",
            "skills#find-unused-skills",
        ))
    truncated = [s["name"] for s in skills if s["truncated"] and s["listed_chars"] > 0]
    if truncated:
        findings.append(finding(
            "P3", "skills-truncated",
            f"{len(truncated)} description(s) dépassent {cap} caractères (coupées dans le listing)",
            "Le texte au-delà du plafond n'est pas vu par Claude pour choisir le skill.",
            "Mettre le cas d'usage principal au début de la description, raccourcir le reste. "
            "Skills concernés : " + ", ".join(sorted(truncated)[:8]) + ("…" if len(truncated) > 8 else "") + ".",
            "skills#skill-descriptions-are-cut-short",
        ))
    # 9. MCP
    if len(mcp["active"]) >= 10:
        findings.append(finding(
            "P2", "mcp-many",
            f"{len(mcp['active'])} serveurs MCP actifs dans les fichiers de configuration",
            "Avec la recherche d'outils, seuls les noms et les instructions des serveurs sont "
            "chargés d'avance, mais chaque serveur ajoute encore du texte à chaque session et à "
            "chaque sous-agent. (Seuil indicatif de cet outil, pas un seuil officiel.)",
            "Dans /mcp, désactiver ceux que vous n'utilisez pas ; préférer un CLI (gh, git, aws…) "
            "quand il fait le même travail.",
            "costs#reduce-mcp-server-overhead",
        ))
    browser = [n for n in mcp["active"] if any(w in n.lower() for w in BROWSER_WORDS)]
    if len(browser) >= 2:
        findings.append(finding(
            "P2", "mcp-browser-duplicates",
            f"{len(browser)} serveurs MCP qui ressemblent à des piles navigateur : " + ", ".join(browser),
            "Des serveurs qui font le même travail dupliquent leurs instructions dans le contexte.",
            "En garder un seul par usage (/mcp, puis désactiver les autres).",
            "costs#reduce-mcp-server-overhead",
        ))
    # 10. Fichiers mémoire
    for f in memory:
        if f["lines"] > 200:
            findings.append(finding(
                "P2", "memory-long",
                f"{f['path']} : {f['lines']} lignes (recommandation : moins de 200)",
                "Ce fichier est chargé à chaque session ; plus long, il coûte du contexte et nuit à "
                "l'application des consignes.",
                "Déplacer les procédures longues dans des skills (chargés à la demande) et les consignes "
                "limitées à certains fichiers dans .claude/rules/ avec un champ paths:.",
                "memory, costs#move-instructions-from-claudemd-to-skills",
            ))
    if rules["unconditional"] >= 5:
        findings.append(finding(
            "P3", "rules-unconditional",
            f"{rules['unconditional']} règles .claude/rules/ sans champ paths (chargées à chaque session)",
            "Une règle sans paths est chargée en permanence ; avec paths, seulement quand un fichier "
            "correspondant est lu.",
            "Ajouter paths: aux règles qui ne concernent qu'une partie du code.",
            "memory#path-specific-rules",
        ))
    # 11. Fichier de configuration illisible
    for err in settings["errors"] + mcp["errors"]:
        findings.append(finding(
            "P3", "config-unreadable", "Fichier de configuration non lu : " + err,
            "Cette partie de la configuration n'a pas pu être auditée.",
            "Corriger le fichier (JSON valide) puis relancer l'audit.",
            "settings",
        ))

    findings.sort(key=lambda f: (PRIORITY_ORDER[f["priority"]], f["id"]))
    heaviest = sorted(visible, key=lambda s: s["listed_chars"], reverse=True)

    return {
        "tool": "claude-code-token-saver audit.py",
        "version": VERSION,
        "docs_checked": DOCS_DATE,
        "config_dir": short(config_dir),
        "project_dir": short(project_dir),
        "metrics": metrics,
        "overrides": override_states,
        "skills_heaviest": [{"name": s["name"], "scope": s["scope"], "est_tokens": est_tokens(s["listed_chars"])}
                            for s in heaviest[:10]],
        "mcp": {"active": mcp["active"], "disabled": mcp["disabled"], "state_file_found": mcp["state_file_found"]},
        "memory_files": memory,
        "settings_files_read": [scope for scope, _ in settings["layers"]],
        "env_set": sorted(name for name, (val, _s) in env.items() if val is not None),
        "hooks_events": sorted(hooks),
        "findings": findings,
    }


# --------------------------------------------------------------------------
# Sortie
# --------------------------------------------------------------------------

def render_text(report: dict, top: int) -> str:
    m = report["metrics"]
    out = []
    out.append(f"Audit de consommation Claude Code (audit.py {report['version']}, doc du {report['docs_checked']})")
    out.append(f"Configuration : {report['config_dir']}  |  Projet : {report['project_dir']}")
    out.append(f"Fichiers settings lus : {', '.join(report['settings_files_read']) or 'aucun'}")
    out.append("")
    out.append("Mesures (estimations : environ 4 caractères par token, à confirmer avec /context)")
    out.append(f"  Skills : {m['skills_total']} au total, {m['skills_visible']} visibles pour Claude, "
               f"{m['skills_with_description']} avec description complète")
    out.append(f"  Listing des skills : environ {m['skills_listing_est_tokens']} tokens "
               f"(sans skillOverrides : environ {m['skills_listing_without_overrides_est_tokens']})")
    out.append(f"  skillOverrides : {report['overrides']['name-only']} name-only, "
               f"{report['overrides']['user-invocable-only']} user-invocable-only, {report['overrides']['off']} off")
    out.append(f"  Serveurs MCP actifs : {m['mcp_servers_active']} (configurés : {m['mcp_servers_configured']})")
    out.append(f"  Fichiers CLAUDE.md : {m['memory_files']}, environ {m['memory_est_tokens']} tokens, "
               f"le plus long {m['memory_max_lines']} lignes")
    out.append(f"  Sous-agents personnalisés : {m['agents_total']} dont {m['agents_without_model']} sans modèle déclaré, "
               f"{m['agents_with_effort']} avec effort déclaré")
    window = m["autocompact_window"]
    out.append(f"  Seuil de compaction : {window if window is not None else 'non réglé (défaut du modèle)'}")
    if top and report["skills_heaviest"]:
        out.append("")
        out.append(f"Skills les plus lourds dans le listing (top {min(top, len(report['skills_heaviest']))})")
        for s in report["skills_heaviest"][:top]:
            out.append(f"  {s['est_tokens']:>5} tokens  {s['name']} ({s['scope']})")
    out.append("")
    findings = report["findings"]
    if not findings:
        out.append("Constats : aucun. Rien à signaler sur les points vérifiés.")
    else:
        out.append(f"Constats ({len(findings)}), du plus utile au moins utile")
        for i, f in enumerate(findings, 1):
            out.append(f"{i}. [{f['priority']}] {f['title']}")
            out.append(f"   Pourquoi : {f['why']}")
            out.append(f"   Action   : {f['fix']}")
            urls = ", ".join("https://code.claude.com/docs/en/" + part.strip() for part in f["source"].split(","))
            out.append(f"   Source   : {urls}")
    out.append("")
    out.append("Rien n'a été modifié. À mesurer dans Claude Code avant et après : /context, /usage, "
               "/doctor, /skill-doctor.")
    return "\n".join(out)


def render_compare(report: dict, before: dict) -> str:
    out = ["", "Comparaison avec la mesure précédente (négatif = économie)"]
    old = before.get("metrics", {})
    new = report["metrics"]
    keys = ("skills_visible", "skills_with_description", "skills_listing_est_tokens",
            "mcp_servers_active", "memory_est_tokens", "memory_max_lines", "agents_without_model",
            "agents_with_effort",
            "rules_unconditional", "precompact_hooks")
    for key in keys:
        if key in old and isinstance(old[key], (int, float)) and isinstance(new.get(key), (int, float)):
            delta = new[key] - old[key]
            sign = "+" if delta > 0 else ""
            out.append(f"  {key:<32} {old[key]:>7} -> {new[key]:>7}  ({sign}{delta})")
    out.append(f"  {'autocompact_window':<32} {old.get('autocompact_window')} -> {new.get('autocompact_window')}")
    old_f = {f["id"] for f in before.get("findings", [])}
    new_f = {f["id"] for f in report["findings"]}
    out.append(f"  Constats résolus : {', '.join(sorted(old_f - new_f)) or 'aucun'}")
    out.append(f"  Constats nouveaux : {', '.join(sorted(new_f - old_f)) or 'aucun'}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass

    parser = argparse.ArgumentParser(description="Audit en lecture seule de la configuration Claude Code (tokens).")
    parser.add_argument("--config-dir", help="dossier de configuration (défaut : $CLAUDE_CONFIG_DIR ou ~/.claude)")
    parser.add_argument("--project-dir", help="dossier du projet (défaut : dossier courant)")
    parser.add_argument("--json", action="store_true", help="sortie JSON au lieu du texte")
    parser.add_argument("--save", metavar="FICHIER", help="écrit le rapport JSON dans ce fichier (pour --compare)")
    parser.add_argument("--compare", metavar="FICHIER", help="compare avec un rapport JSON enregistré avec --save")
    parser.add_argument("--top", type=int, default=10, help="nombre de skills les plus lourds à lister (défaut 10, 0 = aucun)")
    parser.add_argument("--depense", action="store_true",
                        help="coût estimé (équivalent API) lu dans les transcriptions, par projet, modèle et sous-agents")
    parser.add_argument("--jours", type=int, default=7, metavar="N", help="avec --depense : fenêtre en jours (défaut 7)")
    parser.add_argument("--version", action="version", version=f"audit.py {VERSION}")
    args = parser.parse_args(argv)

    config_dir = Path(args.config_dir or os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude").expanduser()
    project_dir = Path(args.project_dir or os.getcwd()).expanduser().resolve()
    if not config_dir.is_dir():
        print(f"Dossier de configuration introuvable : {short(config_dir)} (utiliser --config-dir)", file=sys.stderr)
        return EXIT_NO_CONFIG

    if args.depense:
        if args.jours < 1:
            print("--jours doit être au moins 1", file=sys.stderr)
            return EXIT_NO_CONFIG
        spend = collect_spend(config_dir.resolve() / "projects", args.jours)
        print(json.dumps(spend, ensure_ascii=False, indent=2) if args.json else render_spend(spend, args.top or 10))
        return EXIT_OK

    report = analyse(config_dir.resolve(), project_dir)

    if args.save:
        try:
            Path(args.save).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            print(f"Écriture impossible : {exc.strerror}", file=sys.stderr)
            return EXIT_NO_CONFIG

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return EXIT_OK

    print(render_text(report, args.top))
    if args.compare:
        before, err = read_json(Path(args.compare))
        if before is None:
            print(f"\nComparaison impossible : {err or 'fichier absent'} ({args.compare})", file=sys.stderr)
        else:
            print(render_compare(report, before))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
