import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import probe_env


class ProbeEnvTests(unittest.TestCase):
    def test_probe_package_reports_missing_package(self):
        result = probe_env.probe_package("definitely_missing_partpipeline_pkg")

        self.assertEqual(result["available"], False)
        self.assertIn("error", result)

    def test_run_command_records_exit_code_and_output(self):
        result = probe_env.run_command([sys.executable, "-c", "print('ok')"], cwd=ROOT)

        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout"].strip(), "ok")

    def test_run_command_accepts_extra_environment(self):
        result = probe_env.run_command(
            [sys.executable, "-c", "import os; print(os.environ['PARTPIPELINE_TEST_ENV'])"],
            cwd=ROOT,
            extra_env={"PARTPIPELINE_TEST_ENV": "present"},
        )

        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout"].strip(), "present")

    def test_write_json_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested" / "probe.json"
            probe_env.write_json(target, {"ok": True})

            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"ok": True})


if __name__ == "__main__":
    unittest.main()
