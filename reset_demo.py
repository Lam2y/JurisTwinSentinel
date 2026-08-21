from pathlib import Path

root = Path(__file__).resolve().parent
paths = [
    root / "backend" / "juristwin_mastery.db",
    root / "backend" / "juristwin_mastery.db-shm",
    root / "backend" / "juristwin_mastery.db-wal",
]
removed = 0
for path in paths:
    if path.exists():
        path.unlink()
        removed += 1
print(f"JurisTwin demo state reset ({removed} database file(s) removed). A fresh governed seed will be created on next launch.")
