#!env python
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QScrollArea,
    QPushButton, QFileDialog
)

from PyQt5.QtGui import QIcon, QPixmap, QKeyEvent
from PyQt5.QtCore import Qt

import sys
import os
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from typing import List


class Viewer(QWidget):
    def __init__(self, filespath: List[str]):
        super().__init__()
        self.setWindowTitle('Maloread')
        self.maxw = 600
        self.index = -1
        self.scroller = None
        self.files_list = filespath
        self.setWindowIcon(QIcon('icon.png'))
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        if self.open_index(0) is None:
            layout.addWidget(self.get_footer())
            self.next.setEnabled(False)
            self.prev.setEnabled(False)
        self.resize(self.maxw + 20, 720)

    def open_index(self, index):
        index_len = len(self.files_list)
        if index < 0 or index >= index_len:
            return
        layout = self.layout()
        self.clear(layout)
        self.maxw = 0
        self.filepath = self.files_list[index]
        layout.addWidget(self.get_scroller())
        self.setWindowTitle(f'Maloread: {self.filepath}')
        self.index = index
        self.prev.setEnabled(index > 0)
        self.next.setEnabled(index < index_len - 1)
        return index

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
        self.scroller = scroller_area
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

        button_open = QPushButton('Open')
        button_prev = QPushButton('Previous')
        button_next = QPushButton('Next')

        button_next.clicked.connect(lambda: self.open_index(self.index + 1))
        button_prev.clicked.connect(lambda: self.open_index(self.index - 1))
        button_open.clicked.connect(lambda: self.toggle_file_opening())

        layout = QHBoxLayout()
        layout.addWidget(button_prev)
        layout.addWidget(button_open)
        layout.addWidget(button_quit)
        layout.addWidget(button_next)
        widget = QWidget()
        widget.setLayout(layout)
        self.prev = button_prev
        self.next = button_next
        return widget

    def load_folder(self, layout, path):
        for root, dirs, files in os.walk(path):
            files.sort()
            for f in files:
                if f.startswith('.'):
                    continue
                fullpath = os.path.join(root, f)
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

    def toggle_file_opening(self):
        w = QFileDialog(self)
        w.setNameFilters(('*.cbz', '*.zip'))
        w.setWindowTitle('Please select files to open')
        w.setModal(True)
        w.setFileMode(QFileDialog.ExistingFiles)
        if w.exec():
            files = w.selectedFiles()
            if files:
                self.files_list = files
                self.open_index(0)
                self.resize(self.maxw + 20, self.height())
                return True
        return False

    def keyPressEvent(self, event):
        if type(event) == QKeyEvent:
            key = event.key()
            if key == Qt.Key_F:
                if not self.isFullScreen():
                    self.showFullScreen()
                else:
                    self.showNormal()
            elif key in (Qt.Key_Escape, Qt.Key_Q):
                self.deleteLater()
            elif key == Qt.Key_A:
                self.open_index(self.index - 1)
            elif key == Qt.Key_D:
                self.open_index(self.index + 1)
            elif key == Qt.Key_O:
                self.toggle_file_opening()
            elif key == Qt.Key_Home and self.scroller:
                self.scroller.verticalScrollBar().setValue(0)
            elif key == Qt.Key_End and self.scroller:
                vsb = self.scroller.verticalScrollBar()
                vsb.setValue(vsb.maximum())
            else:
                print(key)
        super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        window = Viewer(sys.argv[1:])
        window.show()
    except IndexError:
        sys.exit(1)
    sys.exit(app.exec_())
