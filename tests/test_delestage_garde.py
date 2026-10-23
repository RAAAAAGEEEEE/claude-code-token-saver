"""Tests de l'exemple examples/delestage_garde.py : hors ligne, bibliothèque standard."""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "examples"))

import delestage_garde as garde  # noqa: E402

SCRIPT = ROOT / "examples" / "delestage_garde.py"


class GardeTests(unittest.TestCase):
    def test_public_content_passes(self):
        garde.verifier_envoi({"id": "a1", "texte": "La tour Eiffel mesure 330 m."}, ["id", "texte"])

    def test_unknown_field_refused(self):
        with self.assertRaises(garde.EnvoiRefuse):
            garde.verifier_envoi({"id": "a1", "utilisateur": "x"}, ["id", "texte"])

    def test_secrets_refused(self):
        faux = [
            "sk-" + "a" * 24,
            "ghp_" + "b" * 30,
            "AKIA" + "C" * 16,
            "Authorization: Bearer " + "d" * 24,
            "-----BEGIN RSA PRIVATE KEY-----",
            "api_key = valeurfictive123",
            "écrire à prenom.nom@example.com",
        ]
        for valeur in faux:
            with self.subTest(valeur=valeur[:12]):
                with self.assertRaises(garde.EnvoiRefuse):
                    garde.verifier_envoi({"texte": valeur}, ["texte"])

    def test_source_code_refused(self):
        with self.assertRaises(garde.EnvoiRefuse):
            garde.verifier_envoi({"texte": "Voici :\ndef f(x):\n    return x"}, ["texte"])

    def test_nested_values_checked(self):
        with self.assertRaises(garde.EnvoiRefuse):
            garde.verifier_envoi({"texte": ["ok", "sk-" + "z" * 20]}, ["texte"])

    def test_cli_exit_codes_and_no_value_echo(self):
        ok = subprocess.run([sys.executable, "-I", str(SCRIPT), "--champs", "texte"],
                            input='{"texte": "bonjour"}', capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0)
        secret = "sk-" + "q" * 24
        ko = subprocess.run([sys.executable, "-I", str(SCRIPT), "--champs", "texte"],
                            input='{"texte": "%s"}' % secret, capture_output=True, text=True)
        self.assertEqual(ko.returncode, 1)
        self.assertNotIn(secret, ko.stdout + ko.stderr)

    def test_no_network_import(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for module in ("socket", "urllib", "http", "requests"):
            self.assertNotIn("import " + module, source)


if __name__ == "__main__":
    unittest.main()
