from pathlib import Path
from time import perf_counter

from libefiling.default_config import defaultImageParams
from libefiling.parse import process_images

# Benchmark target: images/ 以下の tif 画像
image_files = sorted(Path("images").rglob("*.tif"))
if not image_files:
    raise SystemExit("No *.tif files found under images/")

sample_size = min(120, len(image_files))
sample = image_files[:sample_size]
print(f"sample: {sample_size} files")


def run_case(max_workers: int | None, out_root: Path) -> float:
    out_images = out_root / "images"
    out_ocr = out_root / "ocr"
    out_images.mkdir(parents=True, exist_ok=True)
    out_ocr.mkdir(parents=True, exist_ok=True)

    start = perf_counter()
    result = process_images(
        sample,
        out_images,
        out_ocr,
        defaultImageParams,
        "jpn",
        None,
        max_workers=max_workers,
    )
    elapsed = perf_counter() - start
    print(
        f"max_workers={max_workers} elapsed={elapsed:.3f}s items={len(result)}"
    )
    return elapsed


serial_sec = run_case(1, Path("/tmp/libefiling-bench-serial"))
parallel_sec = run_case(0, Path("/tmp/libefiling-bench-auto"))
print(f"speedup: {serial_sec / parallel_sec:.3f}x")
print(f"time_reduction: {(serial_sec - parallel_sec) / serial_sec * 100:.2f}%")
