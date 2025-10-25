from PySide6.QtGui import QGuiApplication


def getAppId() -> str:
    """Get the appId that is the name of the *.desktop file of the application."""
    return QGuiApplication.desktopFileName()
