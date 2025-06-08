import os
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def load_main_config():
    """Load Main.config from several potential locations.

    If the file is missing, return an empty dictionary instead of raising
    an exception to keep the mailing service operational.
    """
    possible_paths = [
        os.path.join(settings.BASE_DIR, "Main.config"),
        os.path.join(settings.BASE_DIR, os.pardir, "Main.config"),
        os.path.join(os.getcwd(), "Main.config"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8-sig") as f:
                    return json.load(f)
            except Exception as exc:  # pragma: no cover - simple logging
                logger.error("Ошибка чтения %s: %s", path, exc)
                return {}
    logger.warning("Main.config not found in expected locations: %s", possible_paths)
    return {}
