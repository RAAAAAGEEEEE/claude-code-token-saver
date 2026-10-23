"""Tests de structure de SKILL.md, du README et des versions : hors ligne, bibliothèque standard."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import audit  # noqa: E402


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


class SkillStructureTests(unittest.TestCase):
    def test_step_zero_comes_before_audit(self):
        text = read("SKILL.md")
        zero = text.find("### 0. Cadrage (questions à l'utilisateur)")
        audit_step = text.find("### 1. Audit")
        self.assertGreater(zero, 0)
        self.assertGreater(audit_step, zero)

    def test_step_zero_content(self):
        text = read("SKILL.md")
        block = text[text.find("### 0. Cadrage"):text.find("### 1. Audit")]
        self.assertIn("AskUserQuestion", block)
        self.assertIn("4 questions au plus", block)
        self.assertIn("2 à 4 options", block)
        for label in ("a) Son accès à Claude", "b) Sa priorité", "c) Son usage", "d) Ce qu'il refuse de sacrifier"):
            self.assertIn(label, block)
        for option in ("Pro", "Max 5x", "Max 20x", "API au paiement à l'usage", "Team ou Enterprise"):
            self.assertIn(option, block)
        self.assertIn("déjà dans la configuration ou dans la conversation", block)

    def test_report_recalls_answers(self):
        text = read("SKILL.md")
        self.assertIn("Rappeler en tête du rapport les réponses de l'étape 0", text)

    def test_readme_how_it_works(self):
        text = read("README.md")
        self.assertIn("## Comment ça marche", text)
        self.assertIn("/claude-code-token-saver", text)
        self.assertIn("https://code.claude.com/docs/en/skills", text)

    def test_organiser_le_travail_section(self):
        text = read("SKILL.md")
        block = text[text.find("## Organiser le travail"):text.find("## Niveaux de preuve")]
        self.assertGreater(len(block), 0)
        for expected in ("Conversation pilote et sessions rattachées", "File de fond sur serveur",
                         "Délester vers un autre fournisseur", "Sorties sans répétition",
                         "100 %", "claude-lot", "docs/ORGANISER-LE-TRAVAIL.md", "examples/delestage_garde.py"):
            self.assertIn(expected, block)

    def test_organiser_le_travail_doc(self):
        self.assertTrue((ROOT / "docs" / "ORGANISER-LE-TRAVAIL.md").exists())
        text = read("docs/ORGANISER-LE-TRAVAIL.md")
        for heading in ("## 1. Une conversation pilote", "## 2. Une file de fond", "## 3. Délester",
                        "## 4. Des sorties sans répétition"):
            self.assertIn(heading, text)
        self.assertIn("constatée, à vérifier", text.lower())
        self.assertIn("https://github.com/RAAAAAGEEEEE/claude-lot", text)
        self.assertIn("ORGANISER-LE-TRAVAIL.md", read("README.md"))

    def test_no_em_dash_in_new_texts(self):
        for name in ("docs/ORGANISER-LE-TRAVAIL.md", "SKILL.md", "CHANGELOG.md"):
            self.assertNotIn("—", read(name), name)

    def test_versions_agree(self):
        skill = re.search(r'version: "([^"]+)"', read("SKILL.md")).group(1)
        changelog = re.search(r"^## \[(\d+\.\d+\.\d+)\]", read("CHANGELOG.md"), re.M).group(1)
        self.assertEqual(skill, audit.VERSION)
        self.assertEqual(skill, changelog)


if __name__ == "__main__":
    unittest.main()
