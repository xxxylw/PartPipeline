from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.runners.base import SubprocessRunner


class RunnerTests(unittest.TestCase):
    def test_runner_captures_stdout_and_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_dir = Path(temp_dir)
            result = SubprocessRunner().run(
                [sys.executable, "-c", "print('hello from runner')"],
                cwd=ROOT,
                logs_dir=logs_dir,
                name="hello",
            )

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.stdout_log.read_text(encoding="utf-8").strip(),
                "hello from runner",
            )
            self.assertEqual(result.stderr_log.read_text(encoding="utf-8"), "")

    def test_runner_dry_run_does_not_execute(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_dir = Path(temp_dir)
            marker = logs_dir / "marker.txt"
            result = SubprocessRunner().run(
                [
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; Path({str(marker)!r}).write_text('bad')",
                ],
                cwd=ROOT,
                logs_dir=logs_dir,
                name="dry",
                dry_run=True,
            )

            self.assertIsNone(result.exit_code)
            self.assertTrue(result.dry_run)
            self.assertFalse(marker.exists())
            self.assertIn("DRY RUN", result.stdout_log.read_text(encoding="utf-8"))

    def test_runner_preserves_nonzero_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = SubprocessRunner().run(
                [sys.executable, "-c", "import sys; sys.exit(7)"],
                cwd=ROOT,
                logs_dir=Path(temp_dir),
                name="fail",
            )

            self.assertEqual(result.exit_code, 7)


if __name__ == "__main__":
    unittest.main()
