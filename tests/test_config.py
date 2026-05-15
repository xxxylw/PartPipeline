from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.config import ConfigError, load_config, resolve_profile


class ConfigTests(unittest.TestCase):
    def test_default_config_loads_local_profile(self) -> None:
        config = load_config(ROOT / "configs" / "default.yaml")
        profile = resolve_profile(config, None)

        self.assertEqual(config.active_profile, "local_wsl")
        self.assertEqual(profile.name, "local_wsl")
        self.assertEqual(profile.sampart3d.env, "part")
        self.assertEqual(
            profile.sampart3d.python,
            Path("/home/rui/miniconda3/envs/part/bin/python"),
        )
        self.assertEqual(profile.output_root, ROOT / "outputs" / "runs")
        self.assertEqual(config.default_mask_scale, "1.0")

    def test_server_profile_contains_known_ssh_identity(self) -> None:
        config = load_config(ROOT / "configs" / "default.yaml")
        profile = resolve_profile(config, "server")

        self.assertIsNotNone(profile.server_ssh)
        self.assertEqual(profile.server_ssh.host_alias, "d5")
        self.assertEqual(profile.server_ssh.hostname, "10.1.6.8")
        self.assertEqual(profile.server_ssh.user, "qzqd5")
        self.assertEqual(profile.server_ssh.port, 19091)

    def test_missing_profile_has_helpful_error(self) -> None:
        config = load_config(ROOT / "configs" / "default.yaml")

        with self.assertRaisesRegex(ConfigError, "missing-profile"):
            resolve_profile(config, "missing-profile")


if __name__ == "__main__":
    unittest.main()
