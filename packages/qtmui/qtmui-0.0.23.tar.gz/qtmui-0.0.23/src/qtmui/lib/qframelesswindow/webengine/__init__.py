# coding: utf-8
import sys

from ..site_packages.qtcompat.QtCore import Qt
from ..site_packages.qtcompat.QtWebEngineWidgets import QWebEngineView
from qframelesswindow import AcrylicWindow, FramelessWindow, FramelessMainWindow, FramelessDialog


class FramelessWebEngineView(QWebEngineView):
    """ Frameless web engine view """

    def __init__(self, parent):
        if sys.platform == "win32" and isinstance(parent.window(), AcrylicWindow):
            parent.window().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        super().__init__(parent=parent)
        self.setHtml("")

        if isinstance(self.window(), (FramelessWindow, FramelessMainWindow, FramelessDialog)):
            self.window().updateFrameless()