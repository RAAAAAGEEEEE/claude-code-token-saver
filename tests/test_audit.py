"""Tests de scripts/audit.py : hors ligne, bibliothèque standard, données fictives.

Lancer : python -m unittest discover -s tests
"""

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import audit  # noqa: E402

SECRET_VALUES = ("sk-ant-FAKESECRET-123", "ghp_FAKETOKEN456", "hunter2-FAKEPASSWORD", "FAKEBEARER789")


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_json(path: Path, data) -> Path:
    return write(path, json.dumps(data))


def make_skill(config: Path, name: str, description: str, extra: str = "") -> None:
    write(config / "skills" / name / "SKILL.md",
          f"---\nname: {name}\ndescription: {description}\n{extra}---\n\n# {name}\n")


class AuditTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.home = self.tmp / "home"
        self.config = self.home / ".claude"
        self.project = self.tmp / "project"
        self.config.mkdir(parents=True)
        self.project.mkdir(parents=True)
        clean_env = {k: v for k, v in os.environ.items() if k not in audit.WATCHED_ENV}
        patcher = mock.patch.dict(os.environ, clean_env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        home_patch = mock.patch.object(Path, "home", return_value=self.home)
        home_patch.start()
        self.addCleanup(home_patch.stop)

    def run_audit(self) -> dict:
        return audit.analyse(self.config, self.project)

    def ids(self, report: dict) -> set:
        return {f["id"] for f in report["findings"]}


class FrontmatterTests(unittest.TestCase):
    def test_scalar_quoted_and_folded(self):
        text = ("---\nname: demo\ndescription: >\n  première ligne\n  deuxième ligne\n"
                "when_to_use: \"quand utile\"\ndisable-model-invocation: true\n---\ncorps\n")
        meta = audit.parse_frontmatter(text)
        self.assertEqual(meta["name"], "demo")
        self.assertEqual(meta["description"], "première ligne deuxième ligne")
        self.assertEqual(meta["when_to_use"], "quand utile")
        self.assertEqual(meta["disable-model-invocation"], "true")

    def test_nested_block_does_not_leak(self):
        meta = audit.parse_frontmatter("---\nname: a\nmetadata:\n  version: \"1\"\ndescription: d\n---\n")
        self.assertEqual(meta["description"], "d")
        self.assertEqual(meta["name"], "a")

    def test_no_frontmatter(self):
        self.assertEqual(audit.parse_frontmatter("# juste un titre\n"), {})
        self.assertEqual(audit.parse_frontmatter("---\nname: sans fin\n"), {})


class CompactionTests(AuditTestCase):
    def test_empty_config_flags_compact_window(self):
        report = self.run_audit()
        self.assertIn("compact-window", self.ids(report))
        self.assertIn("subagent-model", self.ids(report))
        self.assertIsNone(report["metrics"]["autocompact_window"])

    def test_setting_clears_compact_finding(self):
        write_json(self.config / "settings.json", {"autoCompactWindow": 400000})
        report = self.run_audit()
        self.assertNotIn("compact-window", self.ids(report))
        self.assertEqual(report["metrics"]["autocompact_window"], 400000)

    def test_env_var_counts(self):
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "300000"}):
            report = self.run_audit()
        self.assertNotIn("compact-window", self.ids(report))

    def test_precompact_hook_flagged_without_command(self):
        write_json(self.config / "settings.json", {"hooks": {"PreCompact": [
            {"matcher": "auto", "hooks": [{"type": "command", "command": "run --token " + SECRET_VALUES[1]}]}]}})
        report = self.run_audit()
        self.assertIn("precompact-hook", self.ids(report))
        self.assertEqual(report["metrics"]["precompact_hooks"], 1)
        self.assertNotIn(SECRET_VALUES[1], json.dumps(report))


class EffortAndModelTests(AuditTestCase):
    def test_heavy_effort_from_settings_env(self):
        write_json(self.config / "settings.json", {"env": {"CLAUDE_CODE_EFFORT_LEVEL": "xhigh"}})
        self.assertIn("effort-heavy", self.ids(self.run_audit()))

    def test_medium_effort_not_flagged(self):
        write_json(self.config / "settings.json", {"env": {"CLAUDE_CODE_EFFORT_LEVEL": "medium"}})
        self.assertNotIn("effort-heavy", self.ids(self.run_audit()))

    def test_model_settings_heavy(self):
        write_json(self.config / "settings.json",
                   {"modelSettings": {"claude-opus-5-5": {"effortLevel": "high"}}})
        self.assertIn("effort-heavy", self.ids(self.run_audit()))

    def test_user_toplevel_effort_note(self):
        write_json(self.config / "settings.json", {"effortLevel": "medium"})
        report = self.run_audit()
        self.assertIn("effort-toplevel-ignored", self.ids(report))
        self.assertNotIn("effort-heavy", self.ids(report))

    def test_subagent_model_set_and_force(self):
        write_json(self.config / "settings.json",
                   {"env": {"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1"}})
        ids = self.ids(self.run_audit())
        self.assertNotIn("subagent-model", ids)
        self.assertIn("subagent-force", ids)

    def test_settings_env_beats_shell_env(self):
        write_json(self.config / "settings.json", {"env": {"CLAUDE_CODE_EFFORT_LEVEL": "medium"}})
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_EFFORT_LEVEL": "max"}):
            report = self.run_audit()
        self.assertNotIn("effort-heavy", self.ids(report))

    def test_project_local_overrides_user(self):
        write_json(self.config / "settings.json", {"ultracode": True})
        write_json(self.project / ".claude" / "settings.local.json", {"ultracode": False})
        self.assertNotIn("ultracode", self.ids(self.run_audit()))

    def test_ultracode_flagged(self):
        write_json(self.config / "settings.json", {"ultracode": True})
        self.assertIn("ultracode", self.ids(self.run_audit()))

    def test_tool_search_and_cache_flags(self):
        write_json(self.config / "settings.json",
                   {"env": {"ENABLE_TOOL_SEARCH": "false", "DISABLE_PROMPT_CACHING": "1"}})
        ids = self.ids(self.run_audit())
        self.assertIn("tool-search-off", ids)
        self.assertIn("prompt-cache-off", ids)

    def test_agents_without_model(self):
        write(self.config / "agents" / "a.md", "---\nname: a\ndescription: x\n---\n")
        write(self.config / "agents" / "b.md", "---\nname: b\ndescription: x\nmodel: sonnet\n---\n")
        metrics = self.run_audit()["metrics"]
        self.assertEqual((metrics["agents_total"], metrics["agents_without_model"]), (2, 1))

    def test_no_agent_definition_flags_missing_effort(self):
        report = self.run_audit()
        self.assertIn("agents-no-effort", self.ids(report))
        self.assertEqual(report["metrics"]["agents_with_effort"], 0)

    def test_agents_without_effort_flagged_with_count(self):
        write(self.config / "agents" / "a.md", "---\nname: a\ndescription: x\nmodel: sonnet\n---\n")
        report = self.run_audit()
        finding = next(f for f in report["findings"] if f["id"] == "agents-no-effort")
        self.assertIn("1", finding["title"])

    def test_one_agent_with_effort_clears_finding(self):
        write(self.config / "agents" / "a.md",
              "---\nname: a\ndescription: x\nmodel: sonnet\neffort: high\n---\n")
        report = self.run_audit()
        self.assertNotIn("agents-no-effort", self.ids(report))
        self.assertEqual(report["metrics"]["agents_with_effort"], 1)

    def test_project_agents_count_too(self):
        write(self.project / ".claude" / "agents" / "p.md",
              "---\nname: p\ndescription: x\nmodel: opus\neffort: medium\n---\n")
        self.assertEqual(self.run_audit()["metrics"]["agents_with_effort"], 1)

    def test_user_toplevel_heavy_effort_is_labelled_ineffective(self):
        write_json(self.config / "settings.json", {"effortLevel": "high"})
        report = self.run_audit()
        heavy = next(f for f in report["findings"] if f["id"] == "effort-heavy")
        self.assertIn("sans effet sur Opus 5.5", heavy["title"])
        self.assertIn("effort-toplevel-ignored", self.ids(report))

    def test_effort_env_overrides_agent_effort(self):
        write(self.config / "agents" / "a.md",
              "---\nname: a\ndescription: x\nmodel: sonnet\neffort: high\n---\n")
        write_json(self.config / "settings.json", {"env": {"CLAUDE_CODE_EFFORT_LEVEL": "medium"}})
        self.assertIn("effort-env-overrides-agents", self.ids(self.run_audit()))

    def test_effort_env_auto_or_no_agent_effort_is_not_a_conflict(self):
        write(self.config / "agents" / "a.md",
              "---\nname: a\ndescription: x\nmodel: sonnet\neffort: high\n---\n")
        write_json(self.config / "settings.json", {"env": {"CLAUDE_CODE_EFFORT_LEVEL": "auto"}})
        self.assertNotIn("effort-env-overrides-agents", self.ids(self.run_audit()))
        (self.config / "agents" / "a.md").unlink()
        write_json(self.config / "settings.json", {"env": {"CLAUDE_CODE_EFFORT_LEVEL": "medium"}})
        self.assertNotIn("effort-env-overrides-agents", self.ids(self.run_audit()))

    def test_project_toplevel_heavy_effort_not_labelled_ineffective(self):
        write_json(self.project / ".claude" / "settings.json", {"effortLevel": "high"})
        heavy = next(f for f in self.run_audit()["findings"] if f["id"] == "effort-heavy")
        self.assertNotIn("sans effet", heavy["title"])


class SkillTests(AuditTestCase):
    def test_counts_and_overrides(self):
        for i in range(35):
            make_skill(self.config, f"skill-{i}", "d" * 100)
        report = self.run_audit()
        self.assertEqual(report["metrics"]["skills_total"], 35)
        self.assertIn("skills-many", self.ids(report))
        full = report["metrics"]["skills_listing_est_tokens"]
        overrides = {f"skill-{i}": "name-only" for i in range(30)}
        write_json(self.config / "settings.json", {"skillOverrides": overrides})
        report2 = self.run_audit()
        self.assertLess(report2["metrics"]["skills_listing_est_tokens"], full)
        self.assertEqual(report2["metrics"]["skills_visible"], 35)
        self.assertEqual(report2["metrics"]["skills_with_description"], 5)
        self.assertEqual(report2["overrides"]["name-only"], 30)
        self.assertNotIn("skills-many", self.ids(report2))

    def test_user_invocable_only_and_frontmatter_hide(self):
        make_skill(self.config, "hidden-a", "x" * 50)
        make_skill(self.config, "hidden-b", "x" * 50, "disable-model-invocation: true\n")
        make_skill(self.config, "shown", "x" * 50)
        write_json(self.config / "settings.json", {"skillOverrides": {"hidden-a": "user-invocable-only"}})
        metrics = self.run_audit()["metrics"]
        self.assertEqual(metrics["skills_total"], 3)
        self.assertEqual(metrics["skills_visible"], 1)

    def test_truncated_description_and_custom_cap(self):
        make_skill(self.config, "long", "y" * 2000)
        self.assertIn("skills-truncated", self.ids(self.run_audit()))
        write_json(self.config / "settings.json", {"skillListingMaxDescChars": 3000})
        self.assertNotIn("skills-truncated", self.ids(self.run_audit()))

    def test_synced_and_project_skills_found(self):
        write(self.config / "skills" / "synced" / "from-web" / "SKILL.md", "---\nname: from-web\ndescription: d\n---\n")
        write(self.project / ".claude" / "skills" / "local-one" / "SKILL.md", "---\nname: local-one\ndescription: d\n---\n")
        write(self.config / "skills" / ".trash" / "old" / "SKILL.md", "---\nname: old\ndescription: d\n---\n")
        report = self.run_audit()
        self.assertEqual(report["metrics"]["skills_total"], 2)


class McpTests(AuditTestCase):
    def test_user_local_project_and_disabled(self):
        write_json(self.home / ".claude.json", {
            "mcpServers": {"alpha": {"command": "x", "env": {"TOKEN": SECRET_VALUES[1]}}, "chrome-devtools": {}},
            "projects": {
                str(self.project).replace("\\", "/"): {"mcpServers": {"beta": {}}, "disabledMcpServers": ["alpha"]},
                "/ailleurs": {"mcpServers": {"gamma": {}}},
            }})
        write_json(self.project / ".mcp.json", {"mcpServers": {"playwright": {"headers": {"Authorization": SECRET_VALUES[3]}}}})
        report = self.run_audit()
        self.assertEqual(report["mcp"]["active"], ["beta", "chrome-devtools", "playwright"])
        self.assertEqual(report["mcp"]["disabled"], ["alpha"])
        self.assertIn("mcp-browser-duplicates", self.ids(report))
        self.assertNotIn("gamma", json.dumps(report))
        dumped = json.dumps(report)
        for secret in SECRET_VALUES:
            self.assertNotIn(secret, dumped)

    def test_many_servers_flag(self):
        write_json(self.home / ".claude.json", {"mcpServers": {f"s{i}": {} for i in range(12)}})
        self.assertIn("mcp-many", self.ids(self.run_audit()))

    def test_missing_state_file(self):
        report = self.run_audit()
        self.assertFalse(report["mcp"]["state_file_found"])
        self.assertEqual(report["metrics"]["mcp_servers_active"], 0)


class MemoryTests(AuditTestCase):
    def test_long_claude_md_flagged(self):
        write(self.config / "CLAUDE.md", "\n".join(f"ligne {i}" for i in range(250)) + "\n")
        write(self.project / "CLAUDE.md", "court\n@docs/notes.md\n")
        report = self.run_audit()
        self.assertIn("memory-long", self.ids(report))
        self.assertEqual(report["metrics"]["memory_files"], 2)
        self.assertEqual(report["metrics"]["memory_max_lines"], 250)
        self.assertEqual([f["imports"] for f in report["memory_files"]], [0, 1])

    def test_rules_unconditional(self):
        for i in range(6):
            write(self.project / ".claude" / "rules" / f"r{i}.md", "# règle\n")
        write(self.project / ".claude" / "rules" / "scoped.md", "---\npaths:\n  - 'src/**'\n---\nx\n")
        report = self.run_audit()
        self.assertEqual(report["metrics"]["rules_unconditional"], 6)
        self.assertIn("rules-unconditional", self.ids(report))


class RobustnessTests(AuditTestCase):
    def test_invalid_json_does_not_crash(self):
        write(self.config / "settings.json", "{ pas du json")
        report = self.run_audit()
        self.assertIn("config-unreadable", self.ids(report))

    def test_bom_settings_are_read(self):
        (self.config / "settings.json").write_bytes(b"\xef\xbb\xbf" + json.dumps({"autoCompactWindow": 200000}).encode())
        self.assertEqual(self.run_audit()["metrics"]["autocompact_window"], 200000)

    def test_wrong_types_do_not_crash(self):
        write_json(self.config / "settings.json", {"skillOverrides": [], "hooks": {"PreCompact": "oops"},
                                                   "env": "nope", "modelSettings": {"m": 3}})
        self.run_audit()

    def test_output_never_contains_secrets(self):
        write_json(self.config / "settings.json", {
            "env": {"ANTHROPIC_API_KEY": SECRET_VALUES[0], "GITHUB_TOKEN": SECRET_VALUES[1]},
            "apiKeyHelper": "echo " + SECRET_VALUES[2],
            "hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "curl -H " + SECRET_VALUES[3]}]}]},
        })
        write(self.config / "CLAUDE.md", "mot de passe : " + SECRET_VALUES[2] + "\n")
        report = self.run_audit()
        text = audit.render_text(report, 10)
        blob = json.dumps(report) + text
        for secret in SECRET_VALUES:
            self.assertNotIn(secret, blob)

    def test_home_is_masked(self):
        report = self.run_audit()
        self.assertTrue(report["config_dir"].startswith("~"))
        self.assertNotIn(self.home.name + "/", report["config_dir"].replace("~/", ""))


class CliTests(AuditTestCase):
    def tree_hash(self) -> str:
        digest = hashlib.sha256()
        for path in sorted(self.tmp.rglob("*")):
            digest.update(str(path.relative_to(self.tmp)).encode())
            if path.is_file():
                digest.update(path.read_bytes())
                digest.update(str(path.stat().st_mtime_ns).encode())
        return digest.hexdigest()

    def run_cli(self, *args) -> subprocess.CompletedProcess:
        env = {k: v for k, v in os.environ.items()}
        env["PYTHONIOENCODING"] = "utf-8"
        env["HOME"] = str(self.home)
        env["USERPROFILE"] = str(self.home)
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit.py"), "--config-dir", str(self.config),
             "--project-dir", str(self.project), *args],
            capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(self.tmp))

    def test_text_report_and_read_only(self):
        make_skill(self.config, "demo", "une description")
        write_json(self.config / "settings.json", {"model": "sonnet"})
        before = self.tree_hash()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Audit de consommation Claude Code", result.stdout)
        self.assertIn("[P1]", result.stdout)
        self.assertIn("Rien n'a été modifié", result.stdout)
        self.assertEqual(before, self.tree_hash())

    def test_json_output_is_valid(self):
        result = self.run_cli("--json")
        data = json.loads(result.stdout)
        self.assertEqual(data["version"], audit.VERSION)
        self.assertIn("metrics", data)

    def test_missing_config_dir_exit_2(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit.py"),
                                 "--config-dir", str(self.tmp / "nope")],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 2)

    def test_save_and_compare(self):
        for i in range(40):
            make_skill(self.config, f"s{i}", "d" * 200)
        snapshot = self.tmp / "avant.json"
        first = self.run_cli("--save", str(snapshot))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertTrue(snapshot.is_file())
        write_json(self.config / "settings.json",
                   {"autoCompactWindow": 400000, "skillOverrides": {f"s{i}": "name-only" for i in range(40)}})
        second = self.run_cli("--compare", str(snapshot))
        self.assertIn("Comparaison avec la mesure précédente", second.stdout)
        self.assertIn("compact-window", second.stdout)  # listé comme résolu
        self.assertIn("skills_listing_est_tokens", second.stdout)

    def test_compare_with_bad_file_is_not_fatal(self):
        result = self.run_cli("--compare", str(self.tmp / "absent.json"))
        self.assertEqual(result.returncode, 0)
        self.assertIn("Comparaison impossible", result.stderr)

    def test_render_functions_in_process(self):
        report = self.run_audit()
        buf = io.StringIO()
        with redirect_stdout(buf):
            print(audit.render_text(report, 0))
        self.assertNotIn("Skills les plus lourds", buf.getvalue())


class ExamplesTests(AuditTestCase):
    def test_settings_example_is_valid_and_effective(self):
        example = ROOT / "examples" / "settings.example.json"
        data = json.loads(example.read_text(encoding="utf-8"))
        write_json(self.config / "settings.json", data)
        report = self.run_audit()
        ids = self.ids(report)
        self.assertNotIn("compact-window", ids)
        self.assertNotIn("subagent-model", ids)
        self.assertEqual(report["overrides"]["name-only"], 1)
        self.assertEqual(report["overrides"]["user-invocable-only"], 1)

    AGENT_EXPECTED = {
        "executant": ("claude-sonnet-5-5", "medium"),
        "analyste": ("claude-sonnet-5-5", "high"),
        "expert": ("claude-opus-5-5", "medium"),
        "trieur": ("claude-haiku-4-5-20251001", None),
    }

    def test_example_agents_are_valid(self):
        folder = ROOT / "examples" / "agents"
        self.assertEqual(sorted(p.stem for p in folder.glob("*.md")), sorted(self.AGENT_EXPECTED))
        for name, (model, effort) in self.AGENT_EXPECTED.items():
            meta = audit.parse_frontmatter((folder / f"{name}.md").read_text(encoding="utf-8"))
            self.assertEqual(meta["name"], name)
            self.assertTrue(meta["description"])
            self.assertEqual(meta["model"], model)
            self.assertEqual(meta.get("effort"), effort)
            self.assertIn(meta.get("effort"), (None, "low", "medium", "high", "xhigh", "max"))

    def test_example_agents_clear_the_audit_finding(self):
        import shutil
        shutil.copytree(ROOT / "examples" / "agents", self.config / "agents")
        report = self.run_audit()
        self.assertNotIn("agents-no-effort", self.ids(report))
        self.assertEqual(report["metrics"]["agents_total"], 4)
        self.assertEqual(report["metrics"]["agents_with_effort"], 3)
        self.assertEqual(report["metrics"]["agents_without_model"], 0)

    def test_example_trieur_is_read_only_and_light(self):
        meta = audit.parse_frontmatter((ROOT / "examples" / "agents" / "trieur.md").read_text(encoding="utf-8"))
        self.assertEqual(meta["tools"], "Read, Grep, Glob")
        self.assertEqual(meta["omitClaudeMd"], "true")

    def test_install_commands_do_not_overwrite_and_are_documented_twice(self):
        for name in ("README.md", "SKILL.md", "docs/BONNES-PRATIQUES.md", "docs/INSTALLATION.md"):
            self.assertNotIn("cp -n", (ROOT / name).read_text(encoding="utf-8"), name)
        install = (ROOT / "docs" / "INSTALLATION.md").read_text(encoding="utf-8")
        self.assertIn("```powershell", install)
        self.assertIn("examples\\agents", install)
        self.assertIn("existe déjà, ignoré", install)

    def test_claude_md_example_names_every_example_agent(self):
        text = (ROOT / "examples" / "CLAUDE.md.example").read_text(encoding="utf-8")
        for name in self.AGENT_EXPECTED:
            self.assertIn(name, text)

    def test_decision_table_names_every_example_agent(self):
        text = (ROOT / "docs" / "BONNES-PRATIQUES.md").read_text(encoding="utf-8")
        section = text[text.index("## Choisir le sous-agent, le modèle et l'effort"):]
        for name in self.AGENT_EXPECTED:
            self.assertIn(f"`{name}`", section)

    def test_claude_md_example_is_short_and_clean(self):
        text = (ROOT / "examples" / "CLAUDE.md.example").read_text(encoding="utf-8")
        self.assertLess(text.count("\n"), 200)
        self.assertNotIn("\u2014", text)

    def test_no_em_dash_in_repo_docs(self):
        offenders = []
        for path in (list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))
                     + [p for p in (ROOT / "examples").rglob("*") if p.is_file()]):
            if "\u2014" in path.read_text(encoding="utf-8"):
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_internal_links_and_anchors_resolve(self):
        import re

        def slug(heading: str) -> str:
            text = re.sub(r"[`*]", "", heading.strip().lower())
            text = re.sub(r"[^\w\s-]", "", text)
            return re.sub(r"\s", "-", text)

        broken = []
        files = list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))
        for path in files:
            for target, anchor in re.findall(r"\]\(([^)#\s]*)(?:#([^)\s]*))?\)", path.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                dest = path if target == "" else (path.parent / target).resolve()
                if not dest.exists():
                    broken.append(f"{path.name} -> {target}")
                    continue
                if anchor and dest.suffix == ".md":
                    heads = {slug(h) for h in re.findall(r"(?m)^#{1,6}\s+(.*)$", dest.read_text(encoding="utf-8"))}
                    if anchor not in heads:
                        broken.append(f"{path.name} -> {target}#{anchor}")
        self.assertEqual(broken, [])


if __name__ == "__main__":
    unittest.main()
