import argparse
import logging
import sys
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Tuple

from silx.gui import qt

from ..gui.settings import clear_settings
from ..gui.xasmap_viewer import XasMapViewer

_logger = logging.getLogger(__name__)


def _absorb_nonbase_exception(exc_type, exc_value, exc_traceback) -> None:
    if not issubclass(exc_type, Exception):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    _logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def _cli(
    args: Optional[Sequence[str]] = None,
) -> Tuple[Dict[str, Optional[str]], bool, int]:
    parser = argparse.ArgumentParser(description="XAS Map Viewer")
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Zero or more data files to load in the XAS Map Viewer",
    )
    parser.add_argument(
        "--dim0-counter",
        default=None,
        help="X-axis channel name",
    )
    parser.add_argument(
        "--dim1-counter",
        default=None,
        help="Y-axis channel name",
    )
    parser.add_argument(
        "--energy-counter",
        default=None,
        help="Primary beam energy channel name",
    )
    parser.add_argument(
        "--mu-counter",
        default=None,
        help="Mu channel name",
    )
    parser.add_argument(
        "--scan",
        default=None,
        type=str,
        help="Scan number",
    )
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity",
    )

    values = parser.parse_args(args=args)
    select_inputs = {
        "filenames": values.filenames,
        "dim0_counter": values.dim0_counter,
        "dim1_counter": values.dim1_counter,
        "energy_counter": values.energy_counter,
        "mu_counter": values.mu_counter,
        "scan_ranges": values.scan,
    }

    return select_inputs, values.fresh, values.verbose


def main(args: Optional[Sequence[str]] = None):
    logging.basicConfig(level=logging.WARNING)
    sys.excepthook = _absorb_nonbase_exception
    select_inputs, fresh, verbosity = _cli(args=args)

    if verbosity == 1:
        logging.getLogger("ewoksid24").setLevel(logging.INFO)
    elif verbosity == 2:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger("ewoksid24").setLevel(logging.DEBUG)
    elif verbosity >= 3:
        logging.getLogger().setLevel(logging.DEBUG)

    app = qt.QApplication([])
    window = XasMapViewer()

    if fresh:
        clear_settings()

    try:
        window.load_settings()
    except Exception:
        _logger.exception("Failed loading the Qt settings")

    window.add_xasmap(**select_inputs)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
