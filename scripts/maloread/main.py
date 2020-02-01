#!env python
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QScrollArea,
    QPushButton, QSizePolicy
)

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt

import sys
import os
from tempfile import TemporaryDirectory
from zipfile import ZipFile


class Viewer(QWidget):
    def __init__(self, filespath):
        super().__init__()
        self.index = 0
        self.filepath = filespath[self.index]
        self.maxw = 0
        self.setWindowTitle(f'CBZ reader {self.filepath}')
        self.setWindowIcon(QIcon('icon.png'))
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self.get_scroller())
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.resize(self.maxw + 15, 720)

    def get_scroller(self):
        scroller_area = QScrollArea(self)
        scroller_area.setVisible(True)
        scroller_area.setWidgetResizable(True)

        scroller_content = QWidget()
        scroller_layout = QVBoxLayout()
        scroller_layout.setSpacing(0)
        scroller_layout.setStretch(0, 1)
        self.load_cbz(scroller_layout, self.filepath)

        button = QPushButton('Quit')
        button.setToolTip('Exit the window')
        button.clicked.connect(lambda: sys.exit(0))
        scroller_layout.addWidget(button)
        scroller_layout.setContentsMargins(0, 0, 0, 0)
        scroller_content.setLayout(scroller_layout)
        scroller_area.setWidget(scroller_content)
        scroller_area.setWidgetResizable(True)
        scroller_area.verticalScrollBar().setSingleStep(30)
        return scroller_area

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        window = Viewer(sys.argv[1:])
        window.show()
    except IndexError:
        sys.exit(1)
    sys.exit(app.exec_())
