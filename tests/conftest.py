"""Put ``app/`` on ``sys.path`` so its flat modules import as they do at runtime.

``flet_app.py`` does the same via ``sys.path.insert`` before importing its
siblings, so ``data_loader`` can say ``from config import ...``. Tests need the
same path setup to import those modules directly.
"""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
