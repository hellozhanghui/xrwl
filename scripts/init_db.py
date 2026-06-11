import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.database import DB_PATH, init_db

init_db(seed=True)
print(f"initialized {DB_PATH}")
