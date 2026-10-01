"""Tests de scripts/backup.py (copie horodatée avant modification)."""

import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import backup  # noqa: E402


class BackupTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.source = self.tmp / "settings.json"
        self.source.write_text('{"a": 1}', encoding="utf-8")

    def test_copy_has_iso_timestamp_and_same_content(self):
        target = backup.backup(self.source, datetime(2026, 10, 1, 14, 30, 5))
        self.assertEqual(target.name, "settings.json.bak-2026-10-01T14-30-05")
        self.assertEqual(target.read_text(encoding="utf-8"), '{"a": 1}')
        self.assertEqual(self.source.read_text(encoding="utf-8"), '{"a": 1}')

    def test_never_overwrites(self):
        when = datetime(2026, 10, 1, 14, 30, 5)
        backup.backup(self.source, when)
        with self.assertRaises(FileExistsError):
            backup.backup(self.source, when)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            backup.backup(self.tmp / "absent.json")

    def test_cli_success_and_failure(self):
        ok = subprocess.run([sys.executable, str(ROOT / "scripts" / "backup.py"), str(self.source)],
                            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertRegex(ok.stdout.strip(), r"settings\.json\.bak-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$")
        bad = subprocess.run([sys.executable, str(ROOT / "scripts" / "backup.py"), str(self.tmp / "nope")],
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(bad.returncode, 1)
        self.assertIn("ÉCHEC", bad.stderr)
        self.assertTrue(re.search(r"absent", bad.stderr))


if __name__ == "__main__":
    unittest.main()
