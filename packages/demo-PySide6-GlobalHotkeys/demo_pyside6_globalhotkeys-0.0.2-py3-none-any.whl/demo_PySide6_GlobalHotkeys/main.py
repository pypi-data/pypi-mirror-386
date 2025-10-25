import logging
import signal
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6_GlobalHotkeys import Listener, bindHotkeys

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)-15s %(levelname)-8s [%(module)s] %(message)s",
    handlers=[stream_handler],
)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        clientArea = QWidget()
        self.setCentralWidget(clientArea)

        layout = QVBoxLayout()

        self.openHotkeysSettingsButton = QPushButton("Bind Hotkeys")
        self.openHotkeysSettingsButton.clicked.connect(
            lambda: bindHotkeys(
                [
                    (
                        "binding1",
                        {
                            "description": "Binding #1",
                        },
                    ),
                    (
                        "binding2",
                        {
                            "description": "Binding #2",
                        },
                    ),
                ]
            )
        )
        layout.addWidget(self.openHotkeysSettingsButton)

        self.logBox = QTextEdit()
        layout.addWidget(self.logBox)

        clientArea.setLayout(layout)

        self.hotkeyListener = Listener()
        self.hotkeyListener.hotkeyPressed.connect(
            lambda binding: self.logBox.append(f"Hotkey '{binding}' pressed!")
        )
        self.hotkeyListener.hotkeyReleased.connect(
            lambda binding: self.logBox.append(f"Hotkey '{binding}' released!")
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()  # closes the window (quits the app if it's the last window)
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("demo-PySide6-GlobalHotkeys")
    app.setDesktopFileName("demo-PySide6-GlobalHotkeys")

    # Let Ctrl+C in terminal close the application.
    signal.signal(signal.SIGINT, lambda *args: QApplication.quit())
    timer = QTimer()
    timer.start(250)
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 250 ms.

    window = MainWindow()
    window.setWindowTitle(app.applicationName())

    window.resize(640, 480)
    window.show()

    sys.exit(app.exec())
