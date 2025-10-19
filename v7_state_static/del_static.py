# delete_state.py
from pathlib import Path
import sys, os, stat

p = Path(sys.argv[1] if len(sys.argv) > 1 else './state.json').expanduser()

try:
    p.unlink()
    print(f"Deleted: {p.resolve()}")
except FileNotFoundError:
    print(f"Not found: {p.resolve()}")
except PermissionError:
    try:
        os.chmod(p, stat.S_IWRITE)  # gỡ read-only trên Windows
        p.unlink()
        print(f"Deleted (after chmod): {p.resolve()}")
    except Exception as e:
        print(f"Failed: {e}")
