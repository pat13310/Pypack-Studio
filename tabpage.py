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


def make_options_page() -> QtWidgets.QWidget:
    # Créer un widget pour contenir tous les éléments
    content_widget = QtWidgets.QWidget()
    form = QtWidgets.QFormLayout(content_widget)
    form.setVerticalSpacing(12)  # Réduire l'espacement vertical entre les lignes
    
    cmb_backend = QtWidgets.QComboBox()
    cmb_backend.addItems(list(BACKENDS.keys()))
    
    chk_onefile = QtWidgets.QCheckBox("One-file")
    chk_onefile.setChecked(True)
    chk_windowed = QtWidgets.QCheckBox("GUI / sans console")
    chk_windowed.setChecked(True)
    chk_clean = QtWidgets.QCheckBox("Nettoyage --clean")
    chk_clean.setChecked(True)
    chk_console = QtWidgets.QCheckBox("Forcer console")
    
    #tbl_data = AddDataTable()
    
    # Widget pour les répertoires et fichiers à créer
    tbl_directories = AddFilesAndDirectoriesWidget()
    
    ed_hidden = QtWidgets.QPlainTextEdit()
    ed_hidden.setPlaceholderText("module_a\npackage_b.sousmodule\n...")
    #ed_hidden.setMaximumHeight(100)
    
    ed_extra = QtWidgets.QPlainTextEdit()
    ed_extra.setPlaceholderText("Args supplémentaires ligne par ligne, ex: \n--exclude-module some_heavy_pkg\n--onedir")
    #ed_extra.setMaximumHeight(100)
    
    ed_python = LabeledLineEdit("Python (optionnel)")
    ed_python.setText(detect_python_exe())
    
    # Stocker les widgets dans le widget de la page pour y accéder depuis l'extérieur
    content_widget.widgets = {
        'cmb_backend': cmb_backend,
        'chk_onefile': chk_onefile,
        'chk_windowed': chk_windowed,
        'chk_clean': chk_clean,
        'chk_console': chk_console,
        #'tbl_data': tbl_data,
        'tbl_directories': tbl_directories,
        'ed_hidden': ed_hidden,
        'ed_extra': ed_extra,
        'ed_python': ed_python
    }
    
    for row in [
        ("Backend", cmb_backend),
        ("Onefile", chk_onefile),
        ("Fenêtre GUI", chk_windowed),
        ("Nettoyer", chk_clean),
        ("Console", chk_console),
        #("Données embarquées", tbl_data),
        ("Fichiers/Répertoires à copier", tbl_directories),
        ("Hidden imports", ed_hidden),
        ("Args extra", ed_extra),
        ("Python", ed_python),
    ]:
        form.addRow(row[0], row[1])
    
    # Créer un QScrollArea et y ajouter le content_widget
    scroll_area = QtWidgets.QScrollArea()
    scroll_area.setWidget(content_widget)
    scroll_area.setWidgetResizable(True)
    
    return scroll_area


def make_profiles_page() -> QtWidgets.QWidget:
    w = QtWidgets.QWidget()
    v = QtWidgets.QVBoxLayout(w)
    
    lst_profiles = QtWidgets.QListWidget()
    
    btn_new = QtWidgets.QPushButton("Nouveau")
    btn_save = QtWidgets.QPushButton("Enregistrer")
    btn_del = QtWidgets.QPushButton("Supprimer")
    btn_export = QtWidgets.QPushButton("Exporter JSON")
    btn_import = QtWidgets.QPushButton("Importer JSON")
    
    h = QtWidgets.QHBoxLayout()
    for b in (btn_new, btn_save, btn_del, btn_export, btn_import):
        h.addWidget(b)
    h.addStretch(1)
    
    v.addWidget(lst_profiles)
    v.addLayout(h)
    
    # Stocker les widgets dans le widget de la page pour y accéder depuis l'extérieur
    w.widgets = {
        'lst_profiles': lst_profiles,
        'btn_new': btn_new,
        'btn_save': btn_save,
        'btn_del': btn_del,
        'btn_export': btn_export,
        'btn_import': btn_import
    }
    
    return w

def make_install_page() -> QtWidgets.QWidget:
    # Créer un widget pour contenir tous les éléments
    content_widget = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(content_widget)
    
    # Stocker les widgets dans la page pour y accéder depuis l'extérieur
    content_widget.widgets = {}
    
    # Titre de la page
    title_label = QtWidgets.QLabel("Installation de l'application")
    title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
    layout.addWidget(title_label)
    
    # Champ pour le nom de l'application
    name_layout = QtWidgets.QHBoxLayout()
    name_label = QtWidgets.QLabel("Nom de l'application:")
    content_widget.widgets['app_name'] = QtWidgets.QLineEdit()
    content_widget.widgets['app_name'].setText("MyApp")
    
    name_layout.addWidget(name_label)
    name_layout.addWidget(content_widget.widgets['app_name'])
    layout.addLayout(name_layout)
    
    # Champ pour choisir le dossier de destination
    dest_layout = QtWidgets.QHBoxLayout()
    dest_label = QtWidgets.QLabel("Dossier de destination:")
    content_widget.widgets['dest_path'] = QtWidgets.QLineEdit()
    
    # Définir le chemin par défaut (dossier utilisateur)
    import os
    from pathlib import Path
    default_path = str(Path.home() / "MyApp")
    content_widget.widgets['dest_path'].setText(default_path)
    
    browse_btn = QtWidgets.QPushButton("Parcourir...")
    browse_btn.clicked.connect(lambda: _browse_destination(content_widget.widgets['dest_path']))
    
    dest_layout.addWidget(dest_label)
    dest_layout.addWidget(content_widget.widgets['dest_path'])
    dest_layout.addWidget(browse_btn)
    layout.addLayout(dest_layout)
    
    # Champ pour sélectionner une image personnalisée pour le wizard
    image_layout = QtWidgets.QHBoxLayout()
    image_label = QtWidgets.QLabel("Image du wizard (optionnel):")
    content_widget.widgets['wizard_image'] = QtWidgets.QLineEdit()
    content_widget.widgets['wizard_image'].setPlaceholderText("Chemin vers l'image personnalisée")
    
    image_browse_btn = QtWidgets.QPushButton("Parcourir...")
    image_browse_btn.clicked.connect(lambda: _browse_wizard_image(content_widget.widgets['wizard_image']))
    
    image_layout.addWidget(image_label)
    image_layout.addWidget(content_widget.widgets['wizard_image'])
    image_layout.addWidget(image_browse_btn)
    layout.addLayout(image_layout)
    
    # Champs pour configurer les textes du wizard
    texts_group = QtWidgets.QGroupBox("Textes du wizard")
    texts_layout = QtWidgets.QFormLayout(texts_group)
    
    content_widget.widgets['intro_title'] = QtWidgets.QLineEdit()
    content_widget.widgets['intro_subtitle'] = QtWidgets.QLineEdit()
    content_widget.widgets['intro_text'] = QtWidgets.QTextEdit()
    content_widget.widgets['intro_text'].setMaximumHeight(60)
    
    content_widget.widgets['app_info_title'] = QtWidgets.QLineEdit()
    content_widget.widgets['app_info_subtitle'] = QtWidgets.QLineEdit()
    
    content_widget.widgets['components_title'] = QtWidgets.QLineEdit()
    content_widget.widgets['components_subtitle'] = QtWidgets.QLineEdit()
    
    content_widget.widgets['install_options_title'] = QtWidgets.QLineEdit()
    content_widget.widgets['install_options_subtitle'] = QtWidgets.QLineEdit()
    
    content_widget.widgets['destination_title'] = QtWidgets.QLineEdit()
    content_widget.widgets['destination_subtitle'] = QtWidgets.QLineEdit()
    
    content_widget.widgets['summary_title'] = QtWidgets.QLineEdit()
    content_widget.widgets['summary_subtitle'] = QtWidgets.QLineEdit()
    
    # Définir les placeholders avec les textes par défaut
    content_widget.widgets['intro_title'].setPlaceholderText("Bienvenue dans l'assistant de création d'application PySide6")
    content_widget.widgets['intro_subtitle'].setPlaceholderText("Cet assistant va vous aider à créer une structure de base pour votre application.")
    content_widget.widgets['intro_text'].setPlaceholderText("Cette application va créer une structure de base pour une application PySide6 avec les éléments nécessaires pour commencer à développer.\n\nCliquez sur Suivant pour continuer.")
    
    content_widget.widgets['app_info_title'].setPlaceholderText("Informations sur l'application")
    content_widget.widgets['app_info_subtitle'].setPlaceholderText("Veuillez entrer les informations de base pour votre application.")
    
    content_widget.widgets['components_title'].setPlaceholderText("Composants")
    content_widget.widgets['components_subtitle'].setPlaceholderText("Sélectionnez les composants à inclure dans votre application.")
    
    content_widget.widgets['install_options_title'].setPlaceholderText("Options d'installation")
    content_widget.widgets['install_options_subtitle'].setPlaceholderText("Sélectionnez les options d'installation pour votre application.")
    
    content_widget.widgets['destination_title'].setPlaceholderText("Destination")
    content_widget.widgets['destination_subtitle'].setPlaceholderText("Choisissez le répertoire où créer votre application.")
    
    content_widget.widgets['summary_title'].setPlaceholderText("Résumé")
    content_widget.widgets['summary_subtitle'].setPlaceholderText("Voici un résumé de vos choix. Cliquez sur Terminer pour quitter l'assistant.")
    
    texts_layout.addRow("Titre introduction:", content_widget.widgets['intro_title'])
    texts_layout.addRow("Sous-titre introduction:", content_widget.widgets['intro_subtitle'])
    texts_layout.addRow("Texte introduction:", content_widget.widgets['intro_text'])
    texts_layout.addRow("Titre infos app:", content_widget.widgets['app_info_title'])
    texts_layout.addRow("Sous-titre infos app:", content_widget.widgets['app_info_subtitle'])
    texts_layout.addRow("Titre composants:", content_widget.widgets['components_title'])
    texts_layout.addRow("Sous-titre composants:", content_widget.widgets['components_subtitle'])
    texts_layout.addRow("Titre options install:", content_widget.widgets['install_options_title'])
    texts_layout.addRow("Sous-titre options install:", content_widget.widgets['install_options_subtitle'])
    texts_layout.addRow("Titre destination:", content_widget.widgets['destination_title'])
    texts_layout.addRow("Sous-titre destination:", content_widget.widgets['destination_subtitle'])
    texts_layout.addRow("Titre résumé:", content_widget.widgets['summary_title'])
    texts_layout.addRow("Sous-titre résumé:", content_widget.widgets['summary_subtitle'])
    
    layout.addWidget(texts_group)
    
    
    # Bouton installer
    install_btn = QtWidgets.QPushButton("Installer")
    install_btn.setStyleSheet("""
        QPushButton {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #5a9bff, stop: 1 #007acc);
            border: 1px solid #4a4a4a;
            border-radius: 6px;
            padding: 8px 24px;
            color: #ffffff;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #6aafff, stop: 1 #1a8cff);
            border: 1px solid #5a9bff;
        }
        QPushButton:pressed {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #007acc, stop: 1 #5a9bff);
            border: 1px solid #2a2a2a;
        }
    """)
    # Le bouton sera connecté à une fonction de callback dans le code principal
    content_widget.install_btn = install_btn
    
    # Centrer le bouton
    btn_layout = QtWidgets.QHBoxLayout()
    btn_layout.addWidget(install_btn)
    btn_layout.addStretch()
    layout.addLayout(btn_layout)
    
    layout.addStretch()
    
    # Créer un QScrollArea et y ajouter le content_widget
    scroll_area = QtWidgets.QScrollArea()
    scroll_area.setWidget(content_widget)
    scroll_area.setWidgetResizable(True)
    
    return scroll_area

def _browse_destination(dest_widget):
    directory = QtWidgets.QFileDialog.getExistingDirectory(
        None, "Choisir le répertoire de destination"
    )
    if directory:
        dest_widget.setText(directory)

def _browse_wizard_image(image_widget):
    file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
        None, "Sélectionner une image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
    )
    if file_path:
        image_widget.setText(file_path)

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