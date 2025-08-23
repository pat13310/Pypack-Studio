"""
PyPack Studio – MVP

Objectif : une application PySide6 modulaire pour créer de « vrais » exécutables
(Python, PySide6, etc.) à l’aide d’outils comme PyInstaller et Nuitka.

• Architecture en couches : UI (Qt Widgets) ↔ Services (Backends d’empaquetage) ↔ Système
• Backends extensibles (Strategy Pattern) : PyInstallerBackend, NuitkaBackend
• Exécution non bloquante via QProcess (stream logs en direct)
• Profils de build persistés (QSettings) + export/import JSON
• Validation de formulaire, normalisation des chemins, détection venv
• Journalisation en mémoire + export

Dépendances: PySide6, Python 3.10+ (recommandé), pyinstaller et/ou nuitka installés dans l’environnement.

Test rapide :
    python pypack_studio.py

"""
from __future__ import annotations
import json
import os
import shlex
import sys
import textwrap
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from PySide6 import QtCore, QtGui, QtWidgets

APP_ORG = "XenSoft"
APP_NAME = "PyPack Studio"

CUSTOM_STYLE = """
/* Dégradé gris sombre pour la fenêtre principale */
 QMainWindow {
     background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                 stop: 0 #2e2e2e, stop: 1 #1a1a1a);
     color: #ffffff;
 }

 /* Style des boutons */
 QPushButton {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #5a5a5a, stop: 1 #3c3c3c);
     border: 1px solid #4a4a4a;
     border-radius: 6px;
     padding: 6px 12px;
     color: #ffffff;
     font-weight: bold;
 }

 QPushButton:hover {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #6a6a6a, stop: 1 #4c4c4c);
    border: 1px solid #5a9bff;
 }

 QPushButton:pressed {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #3c3c3c, stop: 1 #5a5a5a);
     border: 1px solid #2a2a2a;
 }

 QPushButton:disabled {
     background-color: #3a3a3a;
     color: #6a6a6a;
     border: 1px solid #2a2a2a;
 }

 /* Style pour les boutons plus petits comme ceux de PathPicker */
 QToolButton {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #5a5a5a, stop: 1 #3c3c3c);
     border: 1px solid #4a4a4a;
     border-radius: 4px;
     padding: 2px 4px;
     color: #ffffff;
     font-weight: bold;
 }

 QToolButton:hover {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #6a6a6a, stop: 1 #4c4c4c);
     border: 1px solid #5a9bff;
     
 }

 QToolButton:pressed {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #3c3c3c, stop: 1 #5a5a5a);
     border: 1px solid #2a2a2a;
 }

 /* Style pour les champs de saisie */
 QLineEdit, QPlainTextEdit, QComboBox {
     background-color: #2d2d2d;
     border: 1px solid #4a4a4a;
     border-radius: 4px;
     padding: 4px;
     color: #ffffff;
     selection-background-color: #5a5a5a;
 }

 QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
     border: 1px solid #5a9bff ;
 }

 /* Style pour les labels */
 QLabel {
     color: #e0e0e0;
     padding-top:6px;
 }

 /* Style pour les listes et tableaux */
 QListWidget, QTableWidget {
     background-color: #252525;
     alternate-background-color: #2a2a2a;
     border: 1px solid #4a4a4a;
     border-radius: 4px;
     color: #ffffff;
     gridline-color: #4a4a4a;
 }

 QListWidget::item:selected, QTableWidget::item:selected {
     background-color: #5a5a5a;
 }

 /* Style pour la barre de navigation */
 QListWidget#nav {
     background-color: #252525;
     border: none;
     border-radius: 8px;
     font-size:14px;
     padding: 12px;
 }

 QListWidget#nav::item {
     padding: 30px 15px;
     color: #f0f0f0;
     background-color: #2a2a2a;
     border-radius: 8px;
     margin: 3px ;
     border: 1px solid #3a3a3a;
     font-size:14px;
 }

 QListWidget#nav::item:hover {
     background-color: #353535;
     border: 1px solid #454545;
 }

 QListWidget#nav::item:selected {
     background-color: #353535;
     color: #ffffff;
     border-left: 5px solid #5a9bff;
     font-weight: bold;
 }

 /* Style pour les en-têtes de tableau */
 QHeaderView::section {
     background-color: #3a3a3a;
     color: #ffffff;
     padding: 4px;
     border: 1px solid #4a4a4a;
 }

 /* Style pour les cases à cocher */
 QCheckBox {
     color: #e0e0e0;
 }

 QCheckBox::indicator {
     width: 16px;
     height: 16px;
 }

 QCheckBox::indicator:unchecked {
     border: 1px solid #4a4a4a;
     background-color: #2d2d2d;
 }

 QCheckBox::indicator:checked {
     border: 1px solid #4a4a4a;
     background-color: #5a5a5a;
 }

 QCheckBox::indicator:unchecked:hover {
     border: 1px solid #5a9bff;
 }

 QCheckBox::indicator:checked:hover {
     border: 1px solid #5a9bff;
 }

 /* Style pour la barre de progression */
 QProgressBar {
     border: 1px solid #4a4a4a;
     border-radius: 4px;
     text-align: center;
     background-color: #2d2d2d;
 }

 QProgressBar::chunk {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                       stop: 0 #5a9bff, stop: 0.5 #007acc, stop: 1 #003d7a);
     border-radius: 3px;
 }

"""
# ---------------------------
# Utilitaires
# ---------------------------

def normpath(p: str | Path) -> str:
    if not p:
        return ""
    return str(Path(p).expanduser().resolve())


def which(cmd: str) -> Optional[str]:
    """Retourne le chemin de l'exécutable s'il est trouvable dans PATH."""
    from shutil import which as _which
    return _which(cmd)


def detect_python_exe() -> str:
    return normpath(sys.executable)


def add_data_kv(pairs: List[Tuple[str, str]]) -> List[str]:
    """Convertit une liste (src, dst) en arguments --add-data compatibles PyInstaller.
    Sous Windows le séparateur est ';', sinon ':'
    """
    sep = ';' if os.name == 'nt' else ':'
    out = []
    for src, dst in pairs:
        if not src:
            continue
        srcp = normpath(src)
        if dst:
            out.append(f"{srcp}{sep}{dst}")
        else:
            out.append(f"{srcp}{sep}.")
    return out


# ---------------------------
# Utilitaires pour les répertoires et fichiers
# ---------------------------
def copy_files_and_directories_to_output(paths: List[str], output_dir: str, app_name: str):
    """Copie les répertoires et fichiers spécifiés dans le dossier de sortie."""
    import shutil
    # Construire le chemin du répertoire de l'application
    app_dir = Path(output_dir) / app_name
    # S'assurer que le répertoire de l'application existe
    app_dir.mkdir(parents=True, exist_ok=True)
    
    for path in paths:
        if path.strip():
            src_path = Path(path)
            if src_path.exists():
                if src_path.is_dir():
                    # Copier un répertoire
                    dst_path = app_dir / src_path.name
                    # Créer le répertoire de destination s'il n'existe pas
                    dst_path.mkdir(parents=True, exist_ok=True)
                    # Copier le contenu du répertoire
                    for item in src_path.iterdir():
                        if item.is_dir():
                            shutil.copytree(item, dst_path / item.name, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dst_path)
                else:
                    # Copier un fichier
                    dst_path = app_dir / src_path.name
                    shutil.copy2(src_path, dst_path)
            else:
                # Le fichier ou répertoire source n'existe pas
                pass


# ---------------------------
# Modèle de configuration
# ---------------------------
@dataclass
class BuildConfig:
    project_dir: str = ""
    entry_script: str = ""
    name: str = "MyApp"
    icon_path: str = ""
    backend: str = "pyinstaller"  # "pyinstaller" | "nuitka"
    onefile: bool = True
    windowed: bool = True
    clean: bool = True
    console: bool = False
    add_data: List[Tuple[str, str]] = field(default_factory=list)  # (src, dst)
    directories_to_create: List[str] = field(default_factory=list)  # répertoires à créer dans le paquet
    hidden_imports: List[str] = field(default_factory=list)
    extra_args: List[str] = field(default_factory=list)
    output_dir: str = ""
    python_exe: str = ""  # optionnel : forcer un Python spécifique

    def validate(self) -> Tuple[bool, str]:
        if not self.entry_script:
            return False, "Le script d’entrée est requis."
        if not Path(self.entry_script).exists():
            return False, f"Script introuvable: {self.entry_script}"
        if not self.name:
            return False, "Le nom de l'application est requis."
        if self.icon_path and not Path(self.icon_path).exists():
            return False, f"Icône introuvable: {self.icon_path}"
        if self.backend not in {"pyinstaller", "nuitka"}:
            return False, f"Backend non supporté: {self.backend}"
        return True, ""

    def normalized(self) -> "BuildConfig":
        c = BuildConfig(**asdict(self))
        c.project_dir = normpath(c.project_dir or Path(self.entry_script).parent)
        c.entry_script = normpath(c.entry_script)
        c.icon_path = normpath(c.icon_path)
        c.output_dir = normpath(c.output_dir or str(Path(c.project_dir)/"dist"))
        c.python_exe = normpath(c.python_exe or detect_python_exe())
        c.add_data = [(normpath(a), b) for a, b in self.add_data]
        return c


# ---------------------------
# Backends d’empaquetage
# ---------------------------
class PackagerBackend(QtCore.QObject):
    def build_command(self, cfg: BuildConfig) -> List[str]:
        raise NotImplementedError

    def name(self) -> str:
        return "base"


class PyInstallerBackend(PackagerBackend):
    def name(self) -> str:
        return "pyinstaller"

    def build_command(self, cfg: BuildConfig) -> List[str]:
        # Base
        cmd = [cfg.python_exe, "-m", "PyInstaller"]
        if cfg.clean:
            cmd.append("--clean")
        cmd.extend(["--noconfirm", f"--name={cfg.name}"])
        if cfg.onefile:
            cmd.append("--onefile")
        if cfg.windowed and not cfg.console:
            cmd.append("--windowed")
        if cfg.icon_path:
            cmd.append(f"--icon={cfg.icon_path}")
        if cfg.output_dir:
            cmd.extend(["--distpath", cfg.output_dir])
        # add-data
        for pair in add_data_kv(cfg.add_data):
            cmd.extend(["--add-data", pair])
        # directories to create will be handled by creating placeholder files before build
        # hidden-imports
        for hi in cfg.hidden_imports:
            cmd.extend(["--hidden-import", hi])
        # extra
        cmd.extend(cfg.extra_args)
        # entry
        cmd.append(cfg.entry_script)
        return cmd


class NuitkaBackend(PackagerBackend):
    def name(self) -> str:
        return "nuitka"

    def build_command(self, cfg: BuildConfig) -> List[str]:
        # Nuitka: standalone pour embarquer l'interpréteur + deps
        cmd = [cfg.python_exe, "-m", "nuitka", "--standalone"]
        # --onefile reste optionnel sur Nuitka, plus lent mais pratique
        if cfg.onefile:
            cmd.append("--onefile")
        if cfg.windowed and not cfg.console:
            cmd.append("--windows-disable-console") if os.name == 'nt' else None
        if cfg.icon_path and os.name == 'nt':
            cmd.extend(["--windows-icon-from-ico", cfg.icon_path])
        if cfg.output_dir:
            cmd.extend(["--output-dir", cfg.output_dir])
        # data files
        for src, dst in cfg.add_data:
            # Nuitka utilise --include-data-file=SRC=DST (ou DATA-DIR)
            if src:
                dst_final = dst or os.path.basename(src)
                cmd.append(f"--include-data-file={src}={dst_final}")
        # directories to create will be handled by creating placeholder files before build
        # hidden imports
        for hi in cfg.hidden_imports:
            cmd.extend(["--include-module", hi])
        # nom
        if cfg.name:
            cmd.extend(["--product-name", cfg.name, "--company-name", APP_ORG])
            if os.name == 'nt':
                cmd.extend(["--file-version", "1.0.0", "--product-version", "1.0.0"])
        # extra
        cmd.extend(cfg.extra_args)
        # entry
        cmd.append(cfg.entry_script)
        return cmd


BACKENDS: Dict[str, PackagerBackend] = {
    "pyinstaller": PyInstallerBackend(),
    "nuitka": NuitkaBackend(),
}


# ---------------------------
# Worker: exécution QProcess
# ---------------------------
class BuildWorker(QtCore.QObject):
    started = QtCore.Signal(list)
    line = QtCore.Signal(str)
    finished = QtCore.Signal(int)

    def __init__(self, cmd: List[str], workdir: str | None = None, env: Optional[Dict[str, str]] = None):
        super().__init__()
        self.cmd = cmd
        self.workdir = workdir
        self.env = env or {}
        self.proc = QtCore.QProcess()
        # Important: mode de canal pour récupérer stdout + stderr
        self.proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._on_ready)
        self.proc.finished.connect(self._on_finished)

    def start(self):
        self.started.emit(self.cmd)
        if self.workdir:
            self.proc.setWorkingDirectory(self.workdir)
        # Hériter l'environnement + ajouts
        env = QtCore.QProcessEnvironment.systemEnvironment()
        for k, v in (self.env or {}).items():
            env.insert(k, v)
        self.proc.setProcessEnvironment(env)
        # Lancer
        # Sous Windows, QProcess accepte une commande + liste d'arguments
        program = self.cmd[0]
        args = self.cmd[1:]
        self.proc.start(program, args)

    @QtCore.Slot()
    def _on_ready(self):
        data = self.proc.readAllStandardOutput()
        if data:
            try:
                text = bytes(data).decode(errors='replace')
            except Exception:
                text = str(data)
            for ln in text.splitlines():
                self.line.emit(ln)

    @QtCore.Slot(int, QtCore.QProcess.ExitStatus)
    def _on_finished(self, code: int, _status):
        self.finished.emit(code)

    def kill(self):
        if self.proc.state() != QtCore.QProcess.NotRunning:
            self.proc.kill()


# ---------------------------
# Widgets
# ---------------------------
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


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1100, 720)
        self.settings = QtCore.QSettings(APP_ORG, APP_NAME)
        self._build_in_progress = False

        # ---- Barre latérale
        self.nav = QtWidgets.QListWidget()
        self.nav.setObjectName("nav")
        self.nav.addItems(["Projet", "Options", "Profils", "Sortie & Logs"])
        self.nav.setSpacing(10)
        self.nav.setIconSize(QtCore.QSize(50, 50))  # Agrandir les icônes
        self.nav.currentRowChanged.connect(self._switch_page)
        
        # Ajout des icônes aux onglets
        # Premier onglet "Projet" avec projet.png
        if os.path.exists("projet.png"):
            icon_projet = QtGui.QIcon("projet.png")
            self.nav.item(0).setIcon(icon_projet)
        
        # Deuxième onglet "Options" avec pngegg.png
        if os.path.exists("option.png"):
            icon_options = QtGui.QIcon("option.png")
            self.nav.item(1).setIcon(icon_options)

        # Triosième onglet "Profile" avec profile.png
        if os.path.exists("profile.png"):
            icon_profile = QtGui.QIcon("profile.png")
            self.nav.item(2).setIcon(icon_profile)
        
        # Quatrième onglet "Logs" avec log.png
        if os.path.exists("log.png"):
            icon_log = QtGui.QIcon("log.png")
            self.nav.item(3).setIcon(icon_log)

        
        
        # ---- Pages
        self.pages = QtWidgets.QStackedWidget()
        self.page_project = self._make_project_page()
        self.page_options = self._make_options_page()
        self.page_profiles = self._make_profiles_page()
        self.page_output = self._make_output_page()
        for p in (self.page_project, self.page_options, self.page_profiles, self.page_output):
            self.pages.addWidget(p)

        # ---- Layout principal
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        h = QtWidgets.QHBoxLayout(central)
        h.addWidget(self.nav)
        h.addWidget(self.pages, 1)

        self._load_settings()
        # Définir l'icône par défaut si elle n'est pas déjà définie
        if not self.ed_icon.text():
            default_icon_path = "pypack.ico"
            if os.path.exists(default_icon_path):
                self.ed_icon.setText(default_icon_path)
        self.nav.setCurrentRow(0)

        # Définir l'icône de la fenêtre
        window_icon_path = "pypack.ico"
        if not os.path.exists(window_icon_path):
            window_icon_path = "pypack.png"
        if os.path.exists(window_icon_path):
            self.setWindowIcon(QtGui.QIcon(window_icon_path))

    # ---------------- Pages ----------------
    def _make_project_page(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(w)
        form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        form.setFormAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)

        self.ed_project = PathPicker("", is_file=False)
        self.ed_entry = PathPicker("", is_file=True, placeholder="main.py")
        self.ed_name = LabeledLineEdit("", "MyApp")
        self.ed_icon = PathPicker("", is_file=True)
        self.ed_output = PathPicker("", is_file=False)

        # Actions
        btn_analyze = QtWidgets.QPushButton(" Analyser")
        btn_analyze.clicked.connect(self._analyze_project)
        # Ajouter une icône au bouton Analyser si le fichier existe
        if os.path.exists("search.png"):
            btn_analyze.setIcon(QtGui.QIcon("search.png"))
            btn_analyze.setStyleSheet("padding: 12px 20px 12px 20px; margin-top:12px")
        
        btn_build = QtWidgets.QPushButton(" Construire")
        btn_build.setDefault(True)
        btn_build.clicked.connect(self._on_build_clicked)
        # Ajouter une icône au bouton Construire si le fichier existe
        if os.path.exists("engrenage.png"):
            btn_build.setIcon(QtGui.QIcon("engrenage.png"))
            btn_build.setStyleSheet("padding: 12px 20px 12px 20px; margin-top:12px")
            
        
        btn_clean = QtWidgets.QPushButton(" Nettoyer dist/")
        btn_clean.clicked.connect(self._clean_output)
        # Ajouter une icône au bouton Nettoyer si le fichier existe
        if os.path.exists("balai.png"):
            btn_clean.setIcon(QtGui.QIcon("balai.png"))
            btn_clean.setStyleSheet("padding: 12px 20px 12px 20px; margin-top:12px")
            
            

        grid_buttons = QtWidgets.QHBoxLayout()
        grid_buttons.addWidget(btn_analyze)
        grid_buttons.addStretch(1)
        grid_buttons.addWidget(btn_clean)
        grid_buttons.addWidget(btn_build)
        grid_buttons.setSpacing(12)

        for row in [
            ("Dossier projet", self.ed_project),
            ("Script d’entrée", self.ed_entry),
            ("Nom exécutable", self.ed_name),
            ("Icône (.ico/.icns)", self.ed_icon),
            ("Dossier de sortie", self.ed_output),
        ]:
            form.addRow(row[0], row[1])

        sep = QtWidgets.QFrame(); sep.setFrameShape(QtWidgets.QFrame.HLine)
        form.addRow(sep)
        form.addRow(grid_buttons)
        return w

    def _make_options_page(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(w)

        self.cmb_backend = QtWidgets.QComboBox()
        self.cmb_backend.addItems(list(BACKENDS.keys()))

        self.chk_onefile = QtWidgets.QCheckBox("One-file")
        self.chk_onefile.setChecked(True)
        self.chk_windowed = QtWidgets.QCheckBox("GUI / sans console")
        self.chk_windowed.setChecked(True)
        self.chk_clean = QtWidgets.QCheckBox("Nettoyage --clean")
        self.chk_clean.setChecked(True)
        self.chk_console = QtWidgets.QCheckBox("Forcer console")

        self.tbl_data = AddDataTable()
        
        # Widget pour les répertoires et fichiers à créer
        self.tbl_directories = AddFilesAndDirectoriesWidget()

        self.ed_hidden = QtWidgets.QPlainTextEdit()
        self.ed_hidden.setPlaceholderText("module_a\npackage_b.sousmodule\n...")

        self.ed_extra = QtWidgets.QPlainTextEdit()
        self.ed_extra.setPlaceholderText("Args supplémentaires ligne par ligne, ex: \n--exclude-module some_heavy_pkg\n--onedir")

        self.ed_python = LabeledLineEdit("Python (optionnel)")
        self.ed_python.setText(detect_python_exe())

        for row in [
            ("Backend", self.cmb_backend),
            ("Onefile", self.chk_onefile),
            ("Fenêtre GUI", self.chk_windowed),
            ("Nettoyer", self.chk_clean),
            ("Console", self.chk_console),
            ("Données embarquées", self.tbl_data),
            ("Fichiers/Répertoires à copier", self.tbl_directories),
            ("Hidden imports", self.ed_hidden),
            ("Args extra", self.ed_extra),
            ("Python", self.ed_python),
        ]:
            form.addRow(row[0], row[1])
        return w

    def _make_profiles_page(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)

        self.lst_profiles = QtWidgets.QListWidget()
        self.lst_profiles.itemSelectionChanged.connect(self._on_profile_selected)

        btn_new = QtWidgets.QPushButton("Nouveau")
        btn_save = QtWidgets.QPushButton("Enregistrer")
        btn_del = QtWidgets.QPushButton("Supprimer")
        btn_export = QtWidgets.QPushButton("Exporter JSON")
        btn_import = QtWidgets.QPushButton("Importer JSON")

        btn_new.clicked.connect(self._profile_new)
        btn_save.clicked.connect(self._profile_save)
        btn_del.clicked.connect(self._profile_delete)
        btn_export.clicked.connect(self._profile_export)
        btn_import.clicked.connect(self._profile_import)

        h = QtWidgets.QHBoxLayout()
        for b in (btn_new, btn_save, btn_del, btn_export, btn_import):
            h.addWidget(b)
        h.addStretch(1)

        v.addWidget(self.lst_profiles)
        v.addLayout(h)
        return w

    def _make_output_page(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        self.txt_log = QtWidgets.QTextEdit()
        self.txt_log.setReadOnly(True)
        self.lbl_status = QtWidgets.QLabel("En attente de commande...")
        
        # Barre de progression
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        
        h = QtWidgets.QHBoxLayout()
        self.btn_stop = QtWidgets.QPushButton("Stop")
        self.btn_stop.clicked.connect(self._stop_build)
        self.btn_stop.setEnabled(False)
        h.addWidget(self.lbl_status)
        h.addStretch(1)
        h.addWidget(self.btn_stop)
        v.addWidget(self.progress_bar)
        v.addWidget(self.txt_log, 1)
        v.addLayout(h)
        return w

    # ---------------- Logic ----------------
    def _switch_page(self, idx: int):
        self.pages.setCurrentIndex(idx)

    def _append_log(self, text: str, level: str = "info"):
        # Essayer d'extraire le niveau à partir du texte s'il suit le format "PID LEVEL: message"
        import re
        match = re.match(r'^\d+\s+(INFO|WARNING|ERROR|DEBUG|CRITICAL):\s*(.*)', text)
        if match:
            extracted_level, message = match.groups()
            # Utiliser le niveau extrait pour déterminer la couleur et l'icône
            level = extracted_level.lower()  # Assurer que le niveau est en minuscule
            text = message  # Le message est ce qui suit "PID LEVEL:"
        
        color_map = {
            "info": "#edf014",    # Gris clair
            "warning": "#FFA500", # Orange
            "error": "#FF0000"   # Rouge vif
        }
        icon_map = {
            "info": "&#x2139;",     # ℹ️
            "warning": "&#x26A0;",  # ⚠️
            "error": "&#x274C;"     # ❌
        }
        color = color_map.get(level, "#e0e0e0")  # Par défaut gris clair
        icon = icon_map.get(level, "&#x2139;")    # Par défaut ℹ️
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        
        html = f'<div class="log-entry"><span class="timestamp">{timestamp}</span> <span class="icon" style="color: {color};">{icon}</span> <span class="message" style="color: #e0e0e0;"> {text}</span></div>'
        self.txt_log.insertHtml(html)
        self.txt_log.append("")  # Ajouter une nouvelle ligne après l'insertion HTML

    def _status(self, text: str):
        self.lbl_status.setText(text)
    
    def _update_progress(self, text: str):
        # Incrémenter la progression à chaque ligne de log
        current_value = self.progress_bar.value()
        if current_value < 100:
            self.progress_bar.setValue(current_value + 1)
        
        # Réinitialiser la progression si elle atteint 100%
        if self.progress_bar.value() >= 100:
            self.progress_bar.setValue(0)

    def _config_from_ui(self) -> BuildConfig:
        cfg = BuildConfig(
            project_dir=self.ed_project.text(),
            entry_script=self.ed_entry.text(),
            name=self.ed_name.text(),
            icon_path=self.ed_icon.text(),
            backend=self.cmb_backend.currentText(),
            onefile=self.chk_onefile.isChecked(),
            windowed=self.chk_windowed.isChecked(),
            clean=self.chk_clean.isChecked(),
            console=self.chk_console.isChecked(),
            add_data=self.tbl_data.value(),
            directories_to_create=self.tbl_directories.value(),
            hidden_imports=[ln.strip() for ln in self.ed_hidden.toPlainText().splitlines() if ln.strip()],
            extra_args=[ln.strip() for ln in self.ed_extra.toPlainText().splitlines() if ln.strip()],
            output_dir=self.ed_output.text(),
            python_exe=self.ed_python.text(),
        )
        return cfg.normalized()

    def _apply_config_to_ui(self, cfg: BuildConfig):
        self.ed_project.setText(cfg.project_dir)
        self.ed_entry.setText(cfg.entry_script)
        self.ed_name.setText(cfg.name)
        self.ed_icon.setText(cfg.icon_path)
        self.ed_output.setText(cfg.output_dir)
        self.cmb_backend.setCurrentText(cfg.backend)
        self.chk_onefile.setChecked(cfg.onefile)
        self.chk_windowed.setChecked(cfg.windowed)
        self.chk_clean.setChecked(cfg.clean)
        self.chk_console.setChecked(cfg.console)
        self.tbl_data.setValue(cfg.add_data)
        self.tbl_directories.setValue(cfg.directories_to_create)
        self.ed_hidden.setPlainText("\n".join(cfg.hidden_imports))
        self.ed_extra.setPlainText("\n".join(cfg.extra_args))
        self.ed_python.setText(cfg.python_exe)

    # --- Analyse/Nettoyage ---
    def _analyze_project(self):
        cfg = self._config_from_ui()
        ok, msg = cfg.validate()
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Validation", msg)
            return
        # Analyse minimale : vérifier présence de venv et requirements.txt
        proj = Path(cfg.project_dir)
        hints = []
        # venv
        for cand in (".venv", "venv", "env"):
            if (proj/cand).exists():
                hints.append(f"Environnement détecté: {cand}")
                break
        # requirements
        if (proj/"requirements.txt").exists():
            hints.append("requirements.txt détecté. Pensez à geler les versions.")
        # pyside6
        hints.append("Astuce: pour PySide6, incluez Qt plugins via --add-data si nécessaire (styles, platforms, etc.).")
        QtWidgets.QMessageBox.information(self, "Analyse", "\n".join(hints) or "Aucun indice particulier.")

    def _clean_output(self):
        out = self.ed_output.text().strip()
        if not out:
            QtWidgets.QMessageBox.information(self, "Nettoyage", "Aucun dossier de sortie défini.")
            return
        p = Path(out)
        if not p.exists():
            QtWidgets.QMessageBox.information(self, "Nettoyage", f"{out} n'existe pas.")
            return
        
        confirm_box = QtWidgets.QMessageBox(self)
        confirm_box.setWindowTitle("Confirmer")
        confirm_box.setText(f"Supprimer le contenu de {out} ?")
        confirm_box.setIcon(QtWidgets.QMessageBox.Question)
        #confirm = QtWidgets.QMessageBox.question(self, "Confirmer", f"Supprimer le contenu de {out} ?")
        # Ajout des boutons personnalisés
        yes_button = confirm_box.addButton("Oui", QtWidgets.QMessageBox.YesRole)
        no_button = confirm_box.addButton("Non", QtWidgets.QMessageBox.NoRole)
        confirm_box.exec()
        if confirm_box.clickedButton() == yes_button:
            # Suppression prudente : uniquement contenu
            for child in p.iterdir():
                try:
                    if child.is_dir():
                        import shutil
                        shutil.rmtree(child)
                    else:
                        child.unlink(missing_ok=True)
                except Exception as e:
                    self._append_log(f"[CLEAN] Erreur: {e}", "error")
            self._append_log(f"[CLEAN] {out} vidé.", "info")

    # --- Build ---
    def _on_build_clicked(self):
        if self._build_in_progress:
            QtWidgets.QMessageBox.information(self, "Build", "Un build est déjà en cours.")
            return
        cfg = self._config_from_ui()
        ok, msg = cfg.validate()
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Validation", msg)
            self.nav.setCurrentRow(0)
            return
        backend = BACKENDS.get(cfg.backend)
        if backend is None:
            QtWidgets.QMessageBox.warning(self, "Backend", f"Backend inconnu: {cfg.backend}")
            return
        cmd = backend.build_command(cfg)
        # Vérif exe disponible
        tool = cmd[0] if os.path.basename(cmd[0]).lower().startswith("python") else cmd[0]
        if not normpath(tool):
            QtWidgets.QMessageBox.warning(self, "Environnement", "Python introuvable.")
            return
        self._run_build(cmd, workdir=cfg.project_dir)

    def _run_build(self, cmd: List[str], workdir: str):
        self.pages.setCurrentWidget(self.page_output)
        self.txt_log.clear()
        self._build_in_progress = True
        self.btn_stop.setEnabled(True)
        self._status("Construction en cours…")
        
        # Afficher la barre de progression
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = BuildWorker(cmd, workdir=workdir)
        self.worker.started.connect(lambda c: self._append_log("$ " + shlex.join(c)))
        self.worker.line.connect(self._append_log)
        self.worker.line.connect(self._update_progress)  # Mettre à jour la progression avec les logs
        self.worker.finished.connect(self._on_build_finished)
        self.worker.start()

    def _stop_build(self):
        if hasattr(self, 'worker'):
            self.worker.kill()
        self._status("Construction interrompue.")
        self.btn_stop.setEnabled(False)
        self._build_in_progress = False

    def _on_build_finished(self, code: int):
        # Cacher la barre de progression
        self.progress_bar.setVisible(False)
        
        # Copier les répertoires et fichiers spécifiés dans le dossier de sortie
        cfg = self._config_from_ui()
        if cfg.output_dir and cfg.directories_to_create:
            try:
                self._append_log(f"[DEBUG] Chemin de sortie: {cfg.output_dir}", "info")
                self._append_log(f"[DEBUG] Nombre d'éléments à copier: {len(cfg.directories_to_create)}", "info")
                for path in cfg.directories_to_create:
                    self._append_log(f"[DEBUG] Élément à copier: {path}", "info")
                    if Path(path).exists():
                        self._append_log(f"[DEBUG] L'élément existe: {path}", "info")
                    else:
                        self._append_log(f"[DEBUG] L'élément n'existe pas: {path}", "warning")
                copy_files_and_directories_to_output(cfg.directories_to_create, cfg.output_dir, cfg.name)
                self._append_log("[INFO] Répertoires et fichiers copiés dans le dossier de sortie.", "info")
                
                # Vérifier si les fichiers ont été copiés
                for path in cfg.directories_to_create:
                    src_path = Path(path)
                    if src_path.exists():
                        dst_path = Path(cfg.output_dir) / src_path.name
                        if dst_path.exists():
                            self._append_log(f"[DEBUG] Élément copié avec succès: {dst_path}", "info")
                        else:
                            self._append_log(f"[DEBUG] Élément non trouvé après copie: {dst_path}", "warning")
            except Exception as e:
                self._append_log(f"[ERROR] Erreur lors de la copie des répertoires et fichiers: {e}", "error")
        
        if code == 0:
            self._status("Construction réussie.")
        else:
            self._status(f"Construction échouée avec le code {code}.")
        self.btn_stop.setEnabled(False)
        self._build_in_progress = False
        if code == 0:
            QtWidgets.QMessageBox.information(self, "Succès", "Build terminé avec succès.")
        else:
            QtWidgets.QMessageBox.warning(self, "Échec", f"Le build a échoué (code {code}). Consultez les logs.")

    # --- Profils ---
    def _profiles_load_all(self) -> Dict[str, dict]:
        raw = self.settings.value("profiles", "{}")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def _profiles_save_all(self, data: Dict[str, dict]):
        self.settings.setValue("profiles", json.dumps(data, ensure_ascii=False, indent=2))

    def _refresh_profiles_list(self):
        self.lst_profiles.clear()
        for name in sorted(self._profiles_load_all().keys()):
            self.lst_profiles.addItem(name)

    def _on_profile_selected(self):
        item = self.lst_profiles.currentItem()
        if not item:
            return
        name = item.text()
        payload = self._profiles_load_all().get(name, {})
        cfg = BuildConfig(**payload).normalized()
        self._apply_config_to_ui(cfg)

    def _profile_new(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Nouveau profil", "Nom du profil :")
        if not ok or not name.strip():
            return
        data = self._profiles_load_all()
        if name in data:
            QtWidgets.QMessageBox.warning(self, "Profils", "Ce nom existe déjà.")
            return
        cfg = self._config_from_ui()
        data[name] = asdict(cfg)
        self._profiles_save_all(data)
        self._refresh_profiles_list()
        items = self.lst_profiles.findItems(name, QtCore.Qt.MatchExactly)
        if items:
            self.lst_profiles.setCurrentItem(items[0])

    def _profile_save(self):
        item = self.lst_profiles.currentItem()
        if not item:
            QtWidgets.QMessageBox.information(self, "Profils", "Sélectionnez un profil à enregistrer.")
            return
        name = item.text()
        data = self._profiles_load_all()
        data[name] = asdict(self._config_from_ui())
        self._profiles_save_all(data)
        self._append_log(f"[PROFIL] Sauvé: {name}", "info")

    def _profile_delete(self):
        item = self.lst_profiles.currentItem()
        if not item:
            return
        name = item.text()
        data = self._profiles_load_all()
        if name in data:
            del data[name]
            self._profiles_save_all(data)
            self._refresh_profiles_list()
            self._append_log(f"[PROFIL] Supprimé: {name}", "info")

    def _profile_export(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Exporter profils", filter="JSON (*.json)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._profiles_load_all(), f, ensure_ascii=False, indent=2)
        self._append_log(f"[EXPORT] Profils exportés -> {path}", "info")

    def _profile_import(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Importer profils", filter="JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Format invalide")
            self._profiles_save_all(data)
            self._refresh_profiles_list()
            self._append_log(f"[IMPORT] Profils importés depuis {path}", "info")
        except Exception as e:
            self._append_log(f"[IMPORT] Erreur: {e}", "error")
            QtWidgets.QMessageBox.warning(self, "Import", f"Erreur: {e}")

    # --- Settings ---
    def _load_settings(self):
        self.resize(self.settings.value("win/size", QtCore.QSize(1100, 720)))
        self.move(self.settings.value("win/pos", QtCore.QPoint(100, 100)))
        self._refresh_profiles_list()
        last = self.settings.value("last_config", "")
        if last:
            try:
                cfg = BuildConfig(**json.loads(last)).normalized()
                self._apply_config_to_ui(cfg)
            except Exception:
                pass

    def closeEvent(self, e: QtGui.QCloseEvent):
        self.settings.setValue("win/size", self.size())
        self.settings.setValue("win/pos", self.pos())
        self.settings.setValue("last_config", json.dumps(asdict(self._config_from_ui()), ensure_ascii=False))
        super().closeEvent(e)


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setOrganizationName(APP_ORG)
    app.setApplicationName(APP_NAME)
    # Style classique propre
    app.setStyle("Fusion")
    app.setStyleSheet(CUSTOM_STYLE)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
