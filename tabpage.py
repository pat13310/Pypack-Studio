"""
Fichier contenant les pages du stack pour l'application PyPack Studio.
"""

from PySide6 import QtCore, QtGui, QtWidgets
import os
from backends import BACKENDS, BuildConfig
from widgets import LabeledLineEdit, PathPicker, AddDataTable, AddFilesAndDirectoriesWidget
from backends import detect_python_exe


def make_project_page(main_window) -> QtWidgets.QWidget:
    w = QtWidgets.QWidget()
    form = QtWidgets.QFormLayout(w)
    form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    form.setFormAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
    form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)

    main_window.ed_project = PathPicker("", is_file=False)
    main_window.ed_entry = PathPicker("", is_file=True, placeholder="main.py")
    main_window.ed_name = LabeledLineEdit("", "MyApp")
    main_window.ed_icon = PathPicker("", is_file=True)
    main_window.ed_output = PathPicker("", is_file=False)

    # Actions
    btn_analyze = QtWidgets.QPushButton(" Analyser")
    btn_analyze.clicked.connect(main_window._analyze_project)
    # Ajouter une icône au bouton Analyser si le fichier existe
    if os.path.exists("search.png"):
        btn_analyze.setIcon(QtGui.QIcon("search.png"))
        btn_analyze.setStyleSheet("padding: 12px 20px 12px 20px; margin-top:12px")
    
    btn_build = QtWidgets.QPushButton(" Construire")
    btn_build.setDefault(True)
    btn_build.clicked.connect(main_window._on_build_clicked)
    # Ajouter une icône au bouton Construire si le fichier existe
    if os.path.exists("engrenage.png"):
        btn_build.setIcon(QtGui.QIcon("engrenage.png"))
        btn_build.setStyleSheet("padding: 12px 20px 12px 20px; margin-top:12px")
        
    btn_clean = QtWidgets.QPushButton(" Nettoyer dist/")
    btn_clean.clicked.connect(main_window._clean_output)
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
        ("Dossier projet", main_window.ed_project),
        ("Script d’entrée", main_window.ed_entry),
        ("Nom exécutable", main_window.ed_name),
        ("Icône (.ico/.icns)", main_window.ed_icon),
        ("Dossier de sortie", main_window.ed_output),
    ]:
        form.addRow(row[0], row[1])

    sep = QtWidgets.QFrame()
    sep.setFrameShape(QtWidgets.QFrame.HLine)
    form.addRow(sep)
    form.addRow(grid_buttons)
    return w


def make_options_page(main_window) -> QtWidgets.QWidget:
    w = QtWidgets.QWidget()
    form = QtWidgets.QFormLayout(w)

    main_window.cmb_backend = QtWidgets.QComboBox()
    main_window.cmb_backend.addItems(list(BACKENDS.keys()))

    main_window.chk_onefile = QtWidgets.QCheckBox("One-file")
    main_window.chk_onefile.setChecked(True)
    main_window.chk_windowed = QtWidgets.QCheckBox("GUI / sans console")
    main_window.chk_windowed.setChecked(True)
    main_window.chk_clean = QtWidgets.QCheckBox("Nettoyage --clean")
    main_window.chk_clean.setChecked(True)
    main_window.chk_console = QtWidgets.QCheckBox("Forcer console")

    main_window.tbl_data = AddDataTable()
    
    # Widget pour les répertoires et fichiers à créer
    main_window.tbl_directories = AddFilesAndDirectoriesWidget()

    main_window.ed_hidden = QtWidgets.QPlainTextEdit()
    main_window.ed_hidden.setPlaceholderText("module_a\npackage_b.sousmodule\n...")

    main_window.ed_extra = QtWidgets.QPlainTextEdit()
    main_window.ed_extra.setPlaceholderText("Args supplémentaires ligne par ligne, ex: \n--exclude-module some_heavy_pkg\n--onedir")

    main_window.ed_python = LabeledLineEdit("Python (optionnel)")
    main_window.ed_python.setText(detect_python_exe())

    for row in [
        ("Backend", main_window.cmb_backend),
        ("Onefile", main_window.chk_onefile),
        ("Fenêtre GUI", main_window.chk_windowed),
        ("Nettoyer", main_window.chk_clean),
        ("Console", main_window.chk_console),
        ("Données embarquées", main_window.tbl_data),
        ("Fichiers/Répertoires à copier", main_window.tbl_directories),
        ("Hidden imports", main_window.ed_hidden),
        ("Args extra", main_window.ed_extra),
        ("Python", main_window.ed_python),
    ]:
        form.addRow(row[0], row[1])
    return w


def make_profiles_page(main_window) -> QtWidgets.QWidget:
    w = QtWidgets.QWidget()
    v = QtWidgets.QVBoxLayout(w)

    main_window.lst_profiles = QtWidgets.QListWidget()
    main_window.lst_profiles.itemSelectionChanged.connect(main_window._on_profile_selected)

    btn_new = QtWidgets.QPushButton("Nouveau")
    btn_save = QtWidgets.QPushButton("Enregistrer")
    btn_del = QtWidgets.QPushButton("Supprimer")
    btn_export = QtWidgets.QPushButton("Exporter JSON")
    btn_import = QtWidgets.QPushButton("Importer JSON")

    btn_new.clicked.connect(main_window._profile_new)
    btn_save.clicked.connect(main_window._profile_save)
    btn_del.clicked.connect(main_window._profile_delete)
    btn_export.clicked.connect(main_window._profile_export)
    btn_import.clicked.connect(main_window._profile_import)

    h = QtWidgets.QHBoxLayout()
    for b in (btn_new, btn_save, btn_del, btn_export, btn_import):
        h.addWidget(b)
    h.addStretch(1)

    v.addWidget(main_window.lst_profiles)
    v.addLayout(h)
    return w


def make_output_page(main_window) -> QtWidgets.QWidget:
    w = QtWidgets.QWidget()
    v = QtWidgets.QVBoxLayout(w)
    main_window.txt_log = QtWidgets.QTextEdit()
    main_window.txt_log.setReadOnly(True)
    main_window.lbl_status = QtWidgets.QLabel("En attente de commande...")
    
    # Barre de progression
    main_window.progress_bar = QtWidgets.QProgressBar()
    main_window.progress_bar.setVisible(False)
    
    h = QtWidgets.QHBoxLayout()
    main_window.btn_stop = QtWidgets.QPushButton("Stop")
    main_window.btn_stop.clicked.connect(main_window._stop_build)
    main_window.btn_stop.setEnabled(False)
    h.addWidget(main_window.lbl_status)
    h.addStretch(1)
    h.addWidget(main_window.btn_stop)
    v.addWidget(main_window.progress_bar)
    v.addWidget(main_window.txt_log, 1)
    v.addLayout(h)
    return w