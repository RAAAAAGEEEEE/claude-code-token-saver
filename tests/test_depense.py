"""Tests de `audit.py --depense` : transcriptions fictives, hors ligne, bibliothèque standard.

Lancer : python -m unittest discover -s tests
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import audit  # noqa: E402

NOW = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)


def line(msg_id, model, usage, when, text="SECRET-CONTENT-FICTIF"):
    return json.dumps({
        "timestamp": when.isoformat().replace("+00:00", "Z"),
        "message": {"id": msg_id, "model": model, "usage": usage,
                    "content": [{"type": "text", "text": text}]},
    })


def write_lines(path: Path, lines) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class SpendTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = Path(self.tmp.name)
        self.projects = self.config / "projects"

    def test_cost_formula_sonnet(self):
        usage = {"input_tokens": 1_000_000, "cache_read_input_tokens": 1_000_000,
                 "cache_creation_input_tokens": 1_000_000, "output_tokens": 1_000_000}
        self.assertAlmostEqual(audit.usage_cost("claude-sonnet-5-5", usage), 2.0 + 0.2 + 2.5 + 10.0)

    def test_cache_write_one_hour_and_date_suffix(self):
        usage = {"cache_creation_input_tokens": 1_000_000,
                 "cache_creation": {"ephemeral_1h_input_tokens": 1_000_000, "ephemeral_5m_input_tokens": 0}}
        self.assertAlmostEqual(audit.usage_cost("claude-haiku-4-5-20251001", usage), 2.0)

    def test_unknown_model_has_no_price(self):
        self.assertIsNone(audit.usage_cost("modele-inconnu", {"output_tokens": 5}))

    def test_prices_table_is_dated_and_sourced(self):
        self.assertRegex(audit.PRICES_DATE, r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(audit.PRICES_SOURCE.startswith("https://"))

    def test_window_dedup_and_subagents(self):
        recent = NOW - timedelta(days=1)
        old = NOW - timedelta(days=30)
        u = {"output_tokens": 1_000_000}
        write_lines(self.projects / "proj-a" / "s1.jsonl", [
            line("m1", "claude-sonnet-5-5", {"output_tokens": 10}, recent),
            line("m1", "claude-sonnet-5-5", u, recent),  # même message, bloc final : compté une fois
            line("m2", "claude-sonnet-5-5", u, old),      # hors fenêtre
        ])
        write_lines(self.projects / "proj-a" / "s1" / "subagents" / "agent-x.jsonl", [
            line("m3", "claude-opus-5-5", u, recent),
            line("m4", "inconnu", u, recent),
        ])
        spend = audit.collect_spend(self.projects, 5, now=NOW)
        self.assertEqual(spend["messages"], 3)
        self.assertAlmostEqual(spend["by_model"]["claude-sonnet-5-5"], 10.0)
        self.assertAlmostEqual(spend["subagents_by_model"]["claude-opus-5-5"], 20.0)
        self.assertAlmostEqual(spend["total"], 30.0)
        self.assertAlmostEqual(spend["subagents_total"], 20.0)
        self.assertEqual(spend["unpriced"], {"inconnu": 1})

    def test_read_only_and_no_conversation_content(self):
        path = self.projects / "proj-a" / "s1.jsonl"
        write_lines(path, [line("m1", "claude-sonnet-5-5", {"output_tokens": 100}, NOW - timedelta(hours=1))])
        before = path.read_bytes()
        spend = audit.collect_spend(self.projects, 5, now=NOW)
        text = audit.render_spend(spend) + json.dumps(spend)
        self.assertNotIn("SECRET-CONTENT-FICTIF", text)
        self.assertEqual(path.read_bytes(), before)

    def test_cli_option(self):
        write_lines(self.projects / "proj-a" / "s1.jsonl",
                    [line("m1", "claude-sonnet-5-5", {"output_tokens": 1_000_000}, datetime.now(timezone.utc))])
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = audit.main(["--config-dir", str(self.config), "--depense", "--jours", "2"])
        self.assertEqual(code, 0)
        self.assertIn("Total : 10.00 $", buf.getvalue())
        self.assertIn("sous-agents", buf.getvalue().lower())

    def test_missing_projects_dir_gives_zero(self):
        spend = audit.collect_spend(self.projects, 5, now=NOW)
        self.assertEqual(spend["total"], 0.0)
        self.assertIn("Total : 0.00 $", audit.render_spend(spend))


if __name__ == "__main__":
    unittest.main()
