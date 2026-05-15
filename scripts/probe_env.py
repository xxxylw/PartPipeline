#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


PACKAGE_IMPORTS = {
    "torch": "torch",
    "torchvision": "torchvision",
    "torchaudio": "torchaudio",
    "torch_cluster": "torch_cluster",
    "torch_scatter": "torch_scatter",
    "torch_sparse": "torch_sparse",
    "trimesh": "trimesh",
    "numpy": "numpy",
    "pymeshlab": "pymeshlab",
    "diffusers": "diffusers",
    "transformers": "transformers",
    "huggingface_hub": "huggingface_hub",
    "pointcept": "pointcept",
}

DIST_NAMES = {
    "torch_cluster": "torch-cluster",
    "torch_scatter": "torch-scatter",
    "torch_sparse": "torch-sparse",
    "huggingface_hub": "huggingface-hub",
}


def package_version(package: str) -> str | None:
    dist_name = DIST_NAMES.get(package, package)
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def probe_package(package: str) -> dict[str, Any]:
    module_name = PACKAGE_IMPORTS.get(package, package)
    result: dict[str, Any] = {
        "module": module_name,
        "version": package_version(package),
        "available": False,
    }
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # import smoke tests should preserve the exact failure.
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    result["available"] = True
    result["module_file"] = getattr(module, "__file__", None)
    result["module_version"] = getattr(module, "__version__", None)
    return result


def run_command(
    command: list[str],
    cwd: Path,
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        return {
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except Exception as exc:
        return {
            "command": command,
            "exit_code": None,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }


def torch_info() -> dict[str, Any]:
    result = probe_package("torch")
    if not result["available"]:
        return result

    import torch

    result.update(
        {
            "cuda_available": torch.cuda.is_available(),
            "torch_cuda": torch.version.cuda,
            "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "gpu_names": [
                torch.cuda.get_device_name(i)
                for i in range(torch.cuda.device_count())
            ]
            if torch.cuda.is_available()
            else [],
        }
    )
    return result


def collect_probe(project_root: Path) -> dict[str, Any]:
    packages = {name: probe_package(name) for name in PACKAGE_IMPORTS}
    packages["torch"] = torch_info()
    sampart3d_root = project_root / "third_party" / "SAMPart3D"
    holopart_root = project_root / "third_party" / "HoloPart"

    smoke_tests = {
        "sampart3d_runner_help": run_command(
            [sys.executable, "third_party/SAMPart3D/tools/run_sampart3d_object.py", "--help"],
            cwd=project_root,
        ),
        "sampart3d_core_import": run_command(
            [
                sys.executable,
                "-c",
                "import pointcept.datasets; "
                "import pointcept.engines.train; "
                "import pointcept.engines.eval; "
                "import pointcept.models; "
                "print('ok')",
            ],
            cwd=sampart3d_root,
            extra_env={"PYTHONPATH": str(sampart3d_root)},
        ),
        "holopart_inference_help": run_command(
            [sys.executable, "-m", "scripts.inference_holopart", "--help"],
            cwd=holopart_root,
        ),
        "holopart_core_import": run_command(
            [
                sys.executable,
                "-c",
                "from holopart.pipelines.pipeline_holopart import HoloPartPipeline; "
                "from holopart.inference_utils import hierarchical_extract_geometry, flash_extract_geometry; "
                "print('ok')",
            ],
            cwd=holopart_root,
        ),
    }

    return {
        "python": {
            "version": sys.version,
            "version_info": list(sys.version_info[:3]),
            "executable": sys.executable,
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
            "platform": platform.platform(),
            "conda_prefix": os.environ.get("CONDA_PREFIX"),
        },
        "packages": packages,
        "smoke_tests": smoke_tests,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe PartPipeline runtime environment.")
    parser.add_argument("--json", type=Path, required=True, help="Output JSON path.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="PartPipeline project root.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    probe = collect_probe(args.project_root.resolve())
    write_json(args.json, probe)
    print(args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
