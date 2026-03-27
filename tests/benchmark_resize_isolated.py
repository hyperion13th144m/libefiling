"""Run an isolated Pillow vs pillow-simd vs cykooz benchmark in separate virtualenvs."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
ENV_ROOT = ROOT / ".bench-envs"

COMMON_DEPS = [
    "asn1crypto>=1.5.1,<2.0.0",
    "pytesseract>=0.3.13,<0.4.0",
    "pydantic>=2.12.5,<3.0.0",
]

ENV_SPECS = [
    {
        "name": "pillow",
        "packages": ["pillow"],
        "backend": "pillow",
    },
    {
        "name": "pillow-simd",
        "packages": ["pillow-simd"],
        "backend": "pillow",
    },
    {
        "name": "cykooz",
        "packages": ["pillow", "cykooz_resizer"],
        "backend": "cykooz",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=120)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--keep-envs", action="store_true")
    return parser.parse_args()


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def env_python(env_dir: Path) -> Path:
    return env_dir / "bin" / "python"


def setup_env(env_name: str, packages: list[str]) -> Path:
    env_dir = ENV_ROOT / env_name
    if env_dir.exists():
        shutil.rmtree(env_dir)

    print(f"[setup] {env_name}")
    run(["uv", "venv", str(env_dir), "--python", PYTHON])
    python_bin = env_python(env_dir)

    run(["uv", "pip", "install", "--python", str(python_bin), "-e", ".", "--no-deps"])
    run(["uv", "pip", "install", "--python", str(python_bin), *COMMON_DEPS, *packages])
    return env_dir


def benchmark_env(
    env_name: str,
    env_dir: Path,
    backend: str,
    sample_size: int,
    repeats: int,
) -> dict:
    python_bin = env_python(env_dir)
    result = run(
        [
            str(python_bin),
            "docs/benchmark_resize.py",
            "--backend",
            backend,
            "--sample-size",
            str(sample_size),
            "--repeats",
            str(repeats),
            "--json",
        ]
    )
    print(result.stdout)
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    payload["env_name"] = env_name
    return payload


def main() -> int:
    args = parse_args()
    ENV_ROOT.mkdir(exist_ok=True)

    env_dirs: dict[str, Path] = {}
    results: list[dict] = []

    for spec in ENV_SPECS:
        env_dirs[spec["name"]] = setup_env(spec["name"], spec["packages"])

    try:
        for spec in ENV_SPECS:
            results.append(
                benchmark_env(
                    spec["name"],
                    env_dirs[spec["name"]],
                    spec["backend"],
                    args.sample_size,
                    args.repeats,
                )
            )
    finally:
        if not args.keep_envs:
            shutil.rmtree(ENV_ROOT, ignore_errors=True)

    by_name = {result["env_name"]: result for result in results}
    pillow_result = by_name["pillow"]
    fastest = min(results, key=lambda result: result["best"])

    print("=" * 60)
    print("Isolated Comparison")
    print("=" * 60)
    for result in results:
        speedup = pillow_result["best"] / result["best"]
        print(
            f"{result['env_name']:<12} best={result['best']:.3f}s "
            f"throughput={result['throughput']:.0f} ops/s speedup={speedup:.3f}x"
        )
    print(f"fastest      {fastest['env_name']} (best={fastest['best']:.3f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())