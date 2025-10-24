import os
import sys

import matplotlib


def init_matplotlib():
    if _is_headless():
        # For the plot tasks in headless execution
        matplotlib.use("agg")


def _is_headless() -> bool:
    try:
        return not os.isatty(sys.stdout.fileno())
    except AttributeError:
        # celery worker subprocess patches sys.stdout
        return True
