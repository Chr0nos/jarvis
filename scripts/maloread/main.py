#!env python
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QScrollArea,
    QPushButton
)

from PyQt5.QtGui import QIcon, QPixmap, QKeyEvent
from PyQt5.QtCore import Qt

import sys
import os
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from typing import List


KEY_ESCAPE = 16777216
KEY_F = 70
KEY_LEFT = 65
KEY_RIGHT = 68


class Viewer(QWidget):
    def __init__(self, filespath: List[str]):
        super().__init__()
        self.files_list = filespath
        self.setWindowIcon(QIcon('icon.png'))
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.open_index(0)
        self.resize(self.maxw + 20, 720)

    def open_index(self, index):
        if index < 0 or index >= len(self.files_list):
            return
        layout = self.layout()
        self.clear(layout)
        self.maxw = 0
        self.filepath = self.files_list[index]
        layout.addWidget(self.get_scroller())
        self.setWindowTitle(f'Maloread: {self.filepath}')
        self.index = index

    def get_scroller(self):
        scroller_area = QScrollArea(self)
        scroller_area.setVisible(True)
        scroller_area.setWidgetResizable(True)

        scroller_content = QWidget()
        scroller_layout = QVBoxLayout()
        scroller_layout.setSpacing(0)
        scroller_layout.setStretch(0, 1)
        self.load_cbz(scroller_layout, self.filepath)

        scroller_layout.addWidget(self.get_footer())
        scroller_layout.setContentsMargins(0, 0, 0, 0)
        scroller_content.setLayout(scroller_layout)
        scroller_area.setWidget(scroller_content)
        scroller_area.setWidgetResizable(True)
        scroller_area.verticalScrollBar().setSingleStep(30)
        return scroller_area

    def clear(self, layout):
        for _ in range(layout.count()):
            widget = layout.takeAt(0).widget()
            layout.removeWidget(widget)
            widget.deleteLater()

    def get_footer(self) -> QWidget:
        button_quit = QPushButton('Quit')
        button_quit.setToolTip('Exit the window')
        button_quit.clicked.connect(lambda: sys.exit(0))

        button_prev = QPushButton('Previous')
        button_next = QPushButton('Next')

        button_next.clicked.connect(lambda: self.open_index(self.index + 1))
        button_prev.clicked.connect(lambda: self.open_index(self.index - 1))

        layout = QHBoxLayout()
        layout.addWidget(button_prev)
        layout.addWidget(button_quit)
        layout.addWidget(button_next)
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def load_folder(self, layout, path):
        files = os.listdir(path)
        files.sort()
        for f in files:
            if f.startswith('.'):
                continue
            fullpath = os.path.join(path, f)
            layout.addWidget(self.load_picture(fullpath))
        return layout

    def load_picture(self, path):
        # print('loading', path)
        pix = QPixmap(path)
        self.maxw = max(pix.width(), self.maxw)
        # pix.scaledToWidth(6)
        label = QLabel('test', self)
        label.setAlignment(Qt.AlignCenter)
        label.setPixmap(pix)
        label.setStyleSheet("QLabel {background-color: black;}")
        return label

    def unpack_cbz(self, filepath, folder):
        with ZipFile(filepath) as zip_obj:
            zip_obj.extractall(folder)

    def load_cbz(self, layout, filepath):
        with TemporaryDirectory() as folder:
            self.unpack_cbz(filepath, folder)
            self.load_folder(layout, folder)

    def keyPressEvent(self, event):
        if type(event) == QKeyEvent:
            key = event.key()
            if key == KEY_F:
                if not self.isFullScreen():
                    self.showFullScreen()
                else:
                    self.showNormal()
            elif key == KEY_ESCAPE:
                self.deleteLater()
            elif key == KEY_LEFT:
                self.open_index(self.index - 1)
            elif key == KEY_RIGHT:
                self.open_index(self.index + 1)
        super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        window = Viewer(sys.argv[1:])
        window.show()
    except IndexError:
        sys.exit(1)
    sys.exit(app.exec_())
