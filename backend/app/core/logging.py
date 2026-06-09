from __future__ import annotations

import logging


def configure_logging(level: str) -> None:
    resolved_level = (level or "INFO").upper()
    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
