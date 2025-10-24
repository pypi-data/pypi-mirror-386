from itertools import chain, combinations
import platform
from pathlib import Path

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def get_val_dir():
    system = platform.system().lower()
    base = Path(__file__).parent / "Util" / "Grounding"
    if "linux" in system:
        return base / "linux"
    elif "darwin" in system:
        return base / "mac"
    elif "windows" in system:
        return base / "windows"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
