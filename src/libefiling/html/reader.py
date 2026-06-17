import re
from pathlib import Path


def read_htm(path: str | Path) -> list[str]:
    """Read a Shift-JIS encoded HTM file and return lines from the PRE block."""
    data = Path(path).read_bytes()
    text = data.decode("shift_jis", errors="replace")
    m = re.search(r"<PRE>(.*?)</PRE>", text, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)
    return text.splitlines()


def find_htm_file(directory: str | Path) -> Path:
    """Find the single HTM file in a directory."""
    d = Path(directory)
    candidates = list(d.glob("*.HTM")) + list(d.glob("*.htm"))
    if not candidates:
        raise FileNotFoundError(f"No HTM file found in {directory}")
    return candidates[0]
