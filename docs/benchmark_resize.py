"""Benchmark the current PIL implementation in the active environment."""

import argparse
import importlib.metadata
import json
import statistics
from pathlib import Path
from time import perf_counter

import libefiling.image.convert as conv
from libefiling.default_config import defaultImageParams
from libefiling.image.convert import get_size, load_image, resize_image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=120)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--backend", default="pillow")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


args = parse_args()

# --------------------------------------------------------------------------- #
# 画像ファイルの収集
# --------------------------------------------------------------------------- #
DATA_ROOT = Path("images/var/data")
image_files = sorted(DATA_ROOT.rglob("*.tif"))
if not image_files:
    raise SystemExit(f"No *.tif files found under {DATA_ROOT}")

MAX_SAMPLES = 120
sample_files = image_files[: min(args.sample_size, len(image_files))]
print(f"Total *.tif: {len(image_files)}  →  using {len(sample_files)} files")

# --------------------------------------------------------------------------- #
# pillow-simd の有無を確認
# --------------------------------------------------------------------------- #
try:
    simd_ver = importlib.metadata.version("pillow-simd")
    print(f"pillow-simd : {simd_ver}")
except importlib.metadata.PackageNotFoundError:
    simd_ver = None
    print("pillow-simd : not installed  (pillow-simd backend は pillow にフォールバックします)")

try:
    pillow_ver = importlib.metadata.version("Pillow")
except importlib.metadata.PackageNotFoundError:
    pillow_ver = "unknown"
print(f"Pillow      : {pillow_ver}")

if simd_ver is not None:
    print("NOTE: pillow-simd をインストールした環境では PIL 自体が pillow-simd 実装です。")
    print("      このスクリプト内の 'pillow' と 'pillow-simd' は別バイナリ比較ではなく、")
    print("      同じ PIL 実装に対する別コードパス比較になります。")
else:
    print("NOTE: pillow-simd 未導入環境では 'pillow-simd' backend は Pillow にフォールバックします。")
    print("      このスクリプト内の 'pillow' と 'pillow-simd' は別バイナリ比較にはなりません。")

print("      真の比較を行うには、Pillow 環境と pillow-simd 環境を分けて個別に実行してください。")
print()

# --------------------------------------------------------------------------- #
# 画像を事前にメモリへロード（I/O をベンチから除外）
# --------------------------------------------------------------------------- #
print("Loading images into memory...", end=" ", flush=True)
loaded_images = []
for p in sample_files:
    try:
        loaded_images.append(load_image(p))
    except Exception as e:
        print(f"\nSkipping {p}: {e}")
print(f"{len(loaded_images)} images loaded.")
print()

# リサイズターゲット（defaultImageParams の全サイズを使用）
resize_targets = [(p.width, p.height) for p in defaultImageParams]

# --------------------------------------------------------------------------- #
# ベンチマーク本体
# --------------------------------------------------------------------------- #
REPEATS = args.repeats


def run_benchmark(backend: str) -> list[float]:
    """指定バックエンドで全サンプルをリサイズし、1回あたりの経過秒のリストを返す。"""
    conv.RESIZER_BACKEND = backend
    times: list[float] = []
    for _ in range(REPEATS):
        t0 = perf_counter()
        for img in loaded_images:
            for w, h in resize_targets:
                size = get_size(img, w, h)
                resize_image(img, size)
        elapsed = perf_counter() - t0
        times.append(elapsed)
    return times


print(f"[{args.backend}] running ({REPEATS} reps) ...", flush=True)
times = run_benchmark(args.backend)
best = min(times)
avg = statistics.mean(times)
ops = len(loaded_images) * len(resize_targets)
throughput = ops / best

print(f"  best={best:.3f}s  avg={avg:.3f}s  ({ops} resize ops/rep)")
print()
print("=" * 50)
print("  Summary")
print("=" * 50)
print(f"  backend        {args.backend}")
print(f"  pillow         {pillow_ver}")
print(f"  pillow-simd    {simd_ver or 'not installed'}")
print(f"  best           {best:.3f}s")
print(f"  avg            {avg:.3f}s")
print(f"  throughput     {throughput:.0f} ops/s")

if args.json:
    print(
        json.dumps(
            {
                "backend": args.backend,
                "pillow": pillow_ver,
                "pillow_simd": simd_ver,
                "sample_size": len(sample_files),
                "repeats": REPEATS,
                "ops_per_repeat": ops,
                "times": times,
                "best": best,
                "avg": avg,
                "throughput": throughput,
            }
        )
    )
