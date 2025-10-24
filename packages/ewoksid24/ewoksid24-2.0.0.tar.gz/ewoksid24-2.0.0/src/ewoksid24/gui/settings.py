from silx.gui import qt


def get_settings() -> qt.QSettings:
    return qt.QSettings("ewoksid24", "XasMapViewer")


def clear_settings() -> None:
    get_settings().clear()
