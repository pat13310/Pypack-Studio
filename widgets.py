"""
Fichier contenant les classes d'interface utilisateur personnalisées pour l'application PyPack Studio.
"""

from PySide6 import QtCore, QtGui, QtWidgets
from typing import List, Tuple


class LabeledLineEdit(QtWidgets.QWidget):
    textChanged = QtCore.Signal(str)

    def __init__(self, label: str, placeholder: str = "", parent=None):
        super().__init__(parent)
        self._label = QtWidgets.QLabel(label) if label else None
        self._edit = QtWidgets.QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setAlignment(QtCore.Qt.AlignVCenter)
        if self._label:
            lay.addWidget(self._label)
        lay.addWidget(self._edit)
        self._edit.textChanged.connect(self.textChanged)

    def text(self) -> str:
        return self._edit.text()

    def setText(self, s: str):
        self._edit.setText(s)

    def lineEdit(self) -> QtWidgets.QLineEdit:
        return self._edit


class PathPicker(LabeledLineEdit):
    def __init__(self, label: str, is_file=True, placeholder: str = "", parent=None):
        super().__init__(label, placeholder, parent)
        self.is_file = is_file
        btn = QtWidgets.QToolButton()
        btn.setText("…")
        btn.clicked.connect(self._pick)
        self.layout().addWidget(btn)

    def _pick(self):
        if self.is_file:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choisir un fichier")
        else:
            path = QtWidgets.QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if path:
            self.setText(path)


class AddDataTable(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Source", "Destination relative"])
        self.table.horizontalHeader().setStretchLastSection(True)
        btn_add = QtWidgets.QPushButton("Ajouter")
        btn_del = QtWidgets.QPushButton("Supprimer")
        btn_add.clicked.connect(self.add_row)
        btn_del.clicked.connect(self.del_selected)
        v = QtWidgets.QVBoxLayout(self)
        v.addWidget(self.table)
        h = QtWidgets.QHBoxLayout()
        h.addStretch(1)
        h.addWidget(btn_add)
        h.addWidget(btn_del)
        v.addLayout(h)

    def add_row(self, src: str = "", dst: str = ""):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(src))
        self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(dst))

    def del_selected(self):
        for idx in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(idx)

    def value(self) -> List[Tuple[str, str]]:
        out = []
        for r in range(self.table.rowCount()):
            src = self.table.item(r, 0)
            dst = self.table.item(r, 1)
            out.append((src.text().strip() if src else "", dst.text().strip() if dst else ""))
        return out

    def setValue(self, pairs: List[Tuple[str, str]]):
        self.table.setRowCount(0)
        for src, dst in (pairs or []):
            self.add_row(src, dst)


class AddFilesAndDirectoriesWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_widget = QtWidgets.QListWidget()
        btn_add_dir = QtWidgets.QPushButton("Ajouter dossier")
        btn_add_file = QtWidgets.QPushButton("Ajouter fichier")
        btn_del = QtWidgets.QPushButton("Supprimer")
        btn_add_dir.clicked.connect(self.add_directory)
        btn_add_file.clicked.connect(self.add_file)
        btn_del.clicked.connect(self.del_selected)
        v = QtWidgets.QVBoxLayout(self)
        v.addWidget(self.list_widget)
        h = QtWidgets.QHBoxLayout()
        h.addStretch(1)
        h.addWidget(btn_add_dir)
        h.addWidget(btn_add_file)
        h.addWidget(btn_del)
        v.addLayout(h)

    def add_directory(self):
        # Créer une boîte de dialogue pour sélectionner un répertoire
        dialog = QtWidgets.QFileDialog(self, "Sélectionner un répertoire")
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        
        # Traduire les boutons de la boîte de dialogue
        dialog.setLabelText(QtWidgets.QFileDialog.Accept, "Ouvrir")
        dialog.setLabelText(QtWidgets.QFileDialog.Reject, "Annuler")
        
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            directory = dialog.selectedFiles()[0]
            self.list_widget.addItem(directory)

    def add_file(self):
        # Créer une boîte de dialogue pour sélectionner un fichier
        dialog = QtWidgets.QFileDialog(self, "Sélectionner un fichier")
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        
        # Traduire les boutons de la boîte de dialogue
        dialog.setLabelText(QtWidgets.QFileDialog.Accept, "Ouvrir")
        dialog.setLabelText(QtWidgets.QFileDialog.Reject, "Annuler")
        
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            file = dialog.selectedFiles()[0]
            self.list_widget.addItem(file)

    def del_selected(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))

    def value(self) -> List[str]:
        return [self.list_widget.item(i).text().strip() for i in range(self.list_widget.count())]

    def setValue(self, directories: List[str]):
        self.list_widget.clear()
        for directory in directories:
            if directory.strip():
                self.list_widget.addItem(directory.strip())