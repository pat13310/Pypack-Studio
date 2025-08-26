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

from typing import List, Tuple
from PySide6 import QtWidgets, QtCore


from typing import List, Tuple, Optional
from PySide6 import QtWidgets, QtCore, QtGui


from typing import List, Tuple, Optional
from PySide6 import QtWidgets, QtCore, QtGui


class AddDataTable(QtWidgets.QWidget):
    # Signal émis quand les données changent
    dataChanged = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Initialise l'interface utilisateur."""
        # Table
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Source", "Destination relative"])
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # Redimensionnement automatique de la première colonne
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Options d'édition/selection
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked | 
            QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        
        # Alternance des couleurs de lignes
        self.table.setAlternatingRowColors(True)
        
        # Pas de focus sur les lignes vides
        self.table.setShowGrid(True)

        # Boutons
        self.btn_add = QtWidgets.QPushButton("Ajouter")
        self.btn_add.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.btn_add.setToolTip("Ajouter un nouveau fichier")
        
        self.btn_del = QtWidgets.QPushButton("Supprimer")
        self.btn_del.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TrashIcon))
        self.btn_del.setToolTip("Supprimer la ligne sélectionnée")
        
        self.btn_clear = QtWidgets.QPushButton("Tout effacer")
        self.btn_clear.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogResetButton))
        self.btn_clear.setToolTip("Supprimer toutes les lignes")

        # Layout principal
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)  # Pas d'espacement entre les éléments
        v.addWidget(self.table)

        # Barre de boutons alignés à droite - directement collée à la table
        h = QtWidgets.QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)  # Aucune marge
        h.setSpacing(4)
        h.addStretch(1)  # pousse les boutons à droite
        h.addWidget(self.btn_add)
        h.addWidget(self.btn_del)
        h.addWidget(self.btn_clear)

        # Widget conteneur pour les boutons sans marge supplémentaire
        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(h)
        button_widget.setContentsMargins(0, 0, 0, 0)
        
        v.addWidget(button_widget)

        # Ajustement initial
        self.adjust_table_height()
        
        # Menu contextuel
        self._setup_context_menu()

    def _setup_context_menu(self):
        """Configure le menu contextuel."""
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _connect_signals(self):
        """Connecte les signaux aux slots."""
        self.btn_add.clicked.connect(self.add_row)
        self.btn_del.clicked.connect(self.del_selected)
        self.btn_clear.clicked.connect(self.clear_all)
        
        # Émission du signal lors des changements
        self.table.itemChanged.connect(self._on_data_changed)

    def _show_context_menu(self, position):
        """Affiche le menu contextuel."""
        if self.table.itemAt(position) is None:
            return
            
        menu = QtWidgets.QMenu(self)
        
        add_action = menu.addAction("Ajouter")
        add_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogNewFolder))
        add_action.triggered.connect(self.add_row)
        
        del_action = menu.addAction("Supprimer")
        del_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TrashIcon))
        del_action.triggered.connect(self.del_selected)
        del_action.setEnabled(len(self.table.selectedItems()) > 0)
        
        menu.addSeparator()
        
        clear_action = menu.addAction("Tout effacer")
        clear_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogResetButton))
        clear_action.triggered.connect(self.clear_all)
        clear_action.setEnabled(self.table.rowCount() > 0)
        
        menu.exec_(self.table.mapToGlobal(position))

    def _on_data_changed(self):
        """Slot appelé quand les données changent."""
        self.dataChanged.emit()

    def adjust_table_height(self):
        """Ajuste la hauteur de la table en fonction du contenu (min=1 ligne, max=200px)."""
        if self.table.rowCount() == 0:
            # Hauteur minimale pour au moins l'en-tête
            min_height = self.table.horizontalHeader().height() + 25
            self.table.setFixedHeight(min_height)
            return
            
        header_height = self.table.horizontalHeader().height()
        rows_height = sum(self.table.rowHeight(r) for r in range(self.table.rowCount()))
        total_height = header_height + rows_height + 2  # +2 pour bordures minimales
        
        # Contraintes de hauteur
        constrained_height = min(max(total_height, header_height + 25), 200)
        self.table.setFixedHeight(constrained_height)

    def add_row(self, src: str = "", dst: str = ""):
        """Ajoute une nouvelle ligne à la table."""
        if not src:
            src, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, 
                "Choisir un fichier",
                "",
                "Tous les fichiers (*.*)"
            )
            if not src:
                return
                
        # Vérification des doublons
        if self._is_duplicate(src, dst):
            QtWidgets.QMessageBox.warning(
                self, 
                "Doublon détecté", 
                f"Cette source existe déjà: {src}"
            )
            return
            
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(src))
        self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(dst))
        
        self.adjust_table_height()
        self._on_data_changed()

    def _is_duplicate(self, src: str, dst: str) -> bool:
        """Vérifie si une source existe déjà."""
        if not src:
            return False
            
        for r in range(self.table.rowCount()):
            existing_src_item = self.table.item(r, 0)
            if existing_src_item and existing_src_item.text().strip() == src.strip():
                return True
        return False

    def del_selected(self):
        """Supprime les lignes sélectionnées."""
        selected_rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        
        if not selected_rows:
            QtWidgets.QMessageBox.information(
                self, 
                "Aucune sélection", 
                "Veuillez sélectionner une ligne à supprimer."
            )
            return
            
        # Confirmation pour suppression multiple
        if len(selected_rows) > 1:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Confirmation",
                f"Supprimer {len(selected_rows)} lignes ?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                return
        
        for row in selected_rows:
            self.table.removeRow(row)
            
        self.adjust_table_height()
        self._on_data_changed()

    def clear_all(self):
        """Supprime toutes les lignes."""
        if self.table.rowCount() == 0:
            return
            
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirmation",
            "Supprimer toutes les lignes ?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.table.setRowCount(0)
            self.adjust_table_height()
            self._on_data_changed()

    def value(self) -> List[Tuple[str, str]]:
        """Retourne les paires (source, destination) non vides."""
        out = []
        for r in range(self.table.rowCount()):
            src_item = self.table.item(r, 0)
            dst_item = self.table.item(r, 1)
            
            src_text = src_item.text().strip() if src_item else ""
            dst_text = dst_item.text().strip() if dst_item else ""
            
            if src_text:  # Seules les sources non vides sont considérées
                out.append((src_text, dst_text))
        return out

    def setValue(self, pairs: List[Tuple[str, str]]):
        """Définit les paires source-destination."""
        self.table.setRowCount(0)
        for src, dst in (pairs or []):
            # Utilisation directe sans dialogue de fichier
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(src))
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(dst))
            
        self.adjust_table_height()
        self._on_data_changed()

    def get_source_files(self) -> List[str]:
        """Retourne uniquement la liste des fichiers source."""
        return [src for src, _ in self.value()]

    def is_empty(self) -> bool:
        """Vérifie si la table est vide."""
        return len(self.value()) == 0

    def get_row_count(self) -> int:
        """Retourne le nombre de lignes avec des données valides."""
        return len(self.value())


# Exemple d'utilisation
if __name__ == "__main__":
    import sys
    
    app = QtWidgets.QApplication(sys.argv)
    
    # Fenêtre de test
    window = QtWidgets.QMainWindow()
    widget = AddDataTable()
    
    # Connexion du signal pour observer les changements
    widget.dataChanged.connect(lambda: print(f"Données changées: {widget.value()}"))
    
    window.setCentralWidget(widget)
    window.setWindowTitle("Test AddDataTable")
    window.resize(600, 400)
    window.show()
    
    sys.exit(app.exec_())


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
        self.setMaximumHeight(250)
        v.setSpacing(5)  # Réduire l'espacement entre les widgets

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