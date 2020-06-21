#!env python

from PyQt5 import QtWidgets
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt

import sys
import os
import re
from typing import List


class File:
    def __init__(self, filename: str):
        self.filepath = filename

    @property
    def basename(self) -> str:
        return os.path.basename(self.filepath)

    def get_newname(self, fmt, regex):
        if fmt and regex:
            try:
                m = regex.match(self.basename)
                return fmt.format(*m.groups(), **m.groupdict())
            except (Exception) as e:
                # print(type(e), e)
                return None

    def get_filename(self, fmt, regex) -> str:
        new_filename = self.get_newname(fmt, regex)
        return new_filename if new_filename else self.basename

    def rename(self, fmt, regex) -> bool:
        new_name = self.get_filename(fmt, regex)
        if not new_name:
            return False
        root = os.path.dirname(self.filepath)
        new_filepath = os.path.join(root, new_name)
        try:
            os.rename(self.filepath, new_filepath)
            self.filepath = new_filepath
            return True
        except OSError:
            return False

    def __str__(self):
        return self.filepath

    @classmethod
    def get_files_from_dir(cls, folder) -> List['File']:
        if not os.path.exists(folder):
            return []

        def hiden(filename) -> bool:
            if filename[0] == '.':
                return True
            fullpath = os.path.join(folder, filename)
            return not os.path.isfile(fullpath)

        lst = list(
            [cls(os.path.join(folder, f)) for f in os.listdir(folder)
             if not hiden(f)])
        lst.sort(key=lambda x: x.basename)
        return lst


class MainWindow(QtWidgets.QWidget):
    def __init__(self, folder='.'):
        self.folder = os.path.realpath(folder)
        super().__init__()
        self.setWindowTitle('Bwarg')
        self.resize(700, 400)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self._get_controll_section())
        layout.addLayout(self._get_replace_section())
        layout.addWidget(self._get_files_section())
        self.pbar = QtWidgets.QProgressBar()
        layout.addWidget(self.pbar)
        self.setLayout(layout)
        self.replace_edit.setText(r'.+(S\d+E\d+).+\.(\w+)')
        self.scan_folder()
        self.refreshFilesList()

    def scan_folder(self):
        self.files_list = File.get_files_from_dir(self.folder)

    def setRegexValidity(self, valid: bool):
        color = '#ff5050' if not valid else '#ffffff'
        self.replace_edit.setStyleSheet(f'background-color: {color};')

    def get_renaming_pair(self) -> tuple:
        try:
            fmt = self.by_edit.text()
            regex = re.compile(self.replace_edit.text())
            return fmt, regex
        except re.error:
            return (None, None)

    def refreshFilesList(self):
        fmt, regex = self.get_renaming_pair()

        self.files.clear()
        self.pbar.setValue(0)
        self.pbar.setMaximum(len(self.files_list) - 1)
        for i, file in enumerate(self.files_list):
            x = QtWidgets.QListWidgetItem()
            x.setText(file.get_filename(fmt, regex))
            x.setToolTip(file.basename)
            self.files.addItem(x)
            self.pbar.setValue(i)

    def perform_rename(self):
        fmt, regex = self.get_renaming_pair()
        if not fmt or not regex:
            return
        for file in self.files_list:
            file.rename(fmt, regex)

    def _get_controll_section(self):
        layout = QtWidgets.QHBoxLayout()
        left = QtWidgets.QVBoxLayout()
        left.addWidget(self._folder_section())

        layout.addLayout(left)
        layout.addWidget(self._get_actions())
        return layout

    def _folder_section(self) -> QtWidgets.QGroupBox:
        def update_folder(folder):
            self.folder = folder
            self.scan_folder()
            self.refreshFilesList()
            self.folder_edit.setText(folder)

        def browse_folder():
            w = QtWidgets.QFileDialog(self)
            w.setWindowTitle('Choose a folder to open')
            w.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            w.show()
            if not w.exec():
                return
            update_folder(w.selectedFiles()[0])

        folder_section = QtWidgets.QGroupBox('Folder')
        layout = QtWidgets.QHBoxLayout()

        self.folder_edit = QtWidgets.QLineEdit()
        self.folder_edit.setText(self.folder)
        self.folder_edit.editingFinished.connect(
            lambda: update_folder(self.folder_edit.text()))
        browse_btn = QtWidgets.QPushButton()
        browse_btn.setText('...')
        browse_btn.clicked.connect(browse_folder)
        refresh_btn = QtWidgets.QPushButton()
        refresh_btn.setText('Refresh')

        layout.addWidget(self.folder_edit)
        layout.addWidget(browse_btn)
        folder_section.setLayout(layout)
        return folder_section

    def _get_actions(self):
        def rename():
            self.perform_rename()
            self.refreshFilesList()

        actions = QtWidgets.QGroupBox('Actions')
        layout = QtWidgets.QVBoxLayout()
        btn_rename = QtWidgets.QPushButton()
        btn_rename.setText('Rename')
        btn_rename.clicked.connect(rename)
        layout.addWidget(btn_rename)
        actions.setLayout(layout)
        return actions

    def _get_files_section(self):
        files_group = QtWidgets.QGroupBox('Files')
        layout = QtWidgets.QVBoxLayout(files_group)
        files_list = QtWidgets.QListWidget()
        self.files = files_list
        layout.addWidget(files_list)
        return files_group

    def _get_replace_section(self):
        def update_file_list():
            try:
                re.compile(self.replace_edit.text())
                self.setRegexValidity(True)
                self.replace_edit.setToolTip('')
            except Exception as e:
                self.replace_edit.setToolTip(f'Invalid because: {e}')
                self.setRegexValidity(False)
            self.refreshFilesList()

        replace = QtWidgets.QGroupBox('Replace')
        self.replace_edit = QtWidgets.QLineEdit()
        self.replace_edit.setPlaceholderText('Type a regex to rename files')
        self.replace_edit.textEdited.connect(update_file_list)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.replace_edit)
        replace.setLayout(layout)

        by = QtWidgets.QGroupBox('by')
        self.by_edit = QtWidgets.QLineEdit()
        self.by_edit.setPlaceholderText(
            'Enter a format string, {} for capture groups')
        self.by_edit.textEdited.connect(update_file_list)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.by_edit)
        by.setLayout(layout)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(replace)
        layout.addWidget(by)
        return layout

    def keyPressEvent(self, event):
        if type(event) == QKeyEvent:
            key = event.key()
            if key == Qt.Key_Escape:
                self.deleteLater()
        return super().keyPressEvent(event)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    try:
        window = MainWindow(sys.argv[1] if len(sys.argv) > 1 else '.')
        window.show()
    except IndexError:
        sys.exit(1)
    sys.exit(app.exec_())
