import logging
import os
import sys

import buecherhallen.app as app
from buecherhallen.log.custom_formatter import CustomFormatter

log_level = os.environ.get('BH_LOG_LEVEL', 'WARN')
numeric_log_level = getattr(logging, log_level.upper(), None)
if not isinstance(numeric_log_level, int):
    raise ValueError(f"Invalid log level: {log_level}")
logging.basicConfig(level=numeric_log_level)

log = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(CustomFormatter())
log.handlers.clear()
log.addHandler(handler)


def main():
    app.run()


if __name__ == "__main__":
    main()
