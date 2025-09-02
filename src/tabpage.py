"""
Fichier contenant les pages du stack pour l'application PyPack Studio.
"""

from PySide6 import QtCore, QtGui, QtWidgets
import os
from src.backends import BACKENDS, BuildConfig
from src.widgets import LabeledLineEdit, PathPicker, AddDataTable, AddFilesAndDirectoriesWidget
from src.backends import detect_python_exe


class TabPage(QtWidgets.QWidget):
    """Classe de base pour les pages d'onglets."""
    def __init__(self, parent=None):
        super().__init__(parent)


class ProjectTabPage(TabPage):
    setupCheckChanged = QtCore.Signal(int)
    """Page d'onglet pour le projet."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        form = QtWidgets.QFormLayout(self)
        form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        form.setFormAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)

        self.ed_project = PathPicker("", is_file=False)
        self.ed_entry = PathPicker("", is_file=True, placeholder="main.py")
        self.ed_name = LabeledLineEdit("", "MyApp")
        self.ed_icon = PathPicker("", is_file=True)
        self.ed_output = PathPicker("", is_file=False)

        # Option pour afficher le répertoire de sortie à la fin du build
        # Connecter le signal stateChanged à l'émission du signal personnalisé
        self.chk_open_output_dir = QtWidgets.QCheckBox("Afficher le répertoire de sortie à la fin du build")
        self.chk_open_output_dir.setChecked(True)
        
        
        # Option pour créer un setup après le build
        self.chk_create_setup = QtWidgets.QCheckBox("Créer un setup après le build")
        self.chk_create_setup.setChecked(False)
        self.chk_create_setup.stateChanged.connect(self._on_setup_state_changed)
        
        # Actions
        self.btn_analyze = QtWidgets.QPushButton("  Analyser")
        # self.btn_analyze.clicked.connect(lambda: main_window._analyze_project())
        # Ajouter une icône au bouton Analyser si le fichier existe
        if os.path.exists("res/search.png"):
            self.btn_analyze.setIcon(QtGui.QIcon("res/search.png"))
            self.btn_analyze.setStyleSheet("padding: 12px 20px 12px 20px; margin-top:12px")
        
        self.btn_build = QtWidgets.QPushButton("  Construire")
        self.btn_build.setDefault(True)
        self.btn_build.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #5a9bff, stop: 1 #007acc);
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                padding: 12px 28px;
                color: #ffffff;
                font-weight: bold;
                margin-top:12px;
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
        
        # self.btn_build.clicked.connect(lambda: main_window._on_build_clicked())
        # Ajouter une icône au bouton Construire si le fichier existe
        if os.path.exists("res/gear.png"):
            self.btn_build.setIcon(QtGui.QIcon("res/gear.png"))
            
        self.btn_clean = QtWidgets.QPushButton("  Nettoyer dist")
        # self.btn_clean.clicked.connect(lambda: main_window._clean_output())
        # Ajouter une icône au bouton Nettoyer si le fichier existe
        if os.path.exists("res/balai.png"):
            self.btn_clean.setIcon(QtGui.QIcon("res/balai.png"))
            self.btn_clean.setStyleSheet("padding: 12px 20px 12px 20px; margin-top:12px")
            
        grid_buttons = QtWidgets.QHBoxLayout()
        grid_buttons.addWidget(self.btn_analyze)
        grid_buttons.addStretch(1)
        grid_buttons.addWidget(self.btn_clean)
        grid_buttons.addWidget(self.btn_build)
        grid_buttons.setSpacing(12)

        for row in [
            ("Dossier projet", self.ed_project),
            ("Script d’entrée", self.ed_entry),
            ("Nom exécutable", self.ed_name),
            ("Icône (.ico/.icns)", self.ed_icon),
            ("Dossier de sortie", self.ed_output),
        ]:
            form.addRow(row[0], row[1])

        form.addRow(self.chk_open_output_dir)
        form.addRow(self.chk_create_setup)
        
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet("color: #6a9bff;")
        form.addRow(sep)
        form.addRow(grid_buttons)

    def _on_setup_state_changed(self, state):
        # state est déjà un entier (0 ou 2)
        print(f"[DEBUG] tabpage setup_checkbox state={state}")
        self.setupCheckChanged.emit(state)

class OutputTabPage(TabPage):
    """Page d'onglet pour la sortie et les logs."""
    
    # Définir le signal personnalisé
    stopRequested = QtCore.Signal()
    
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self._setup_ui()
        
    def _scroll_to_bottom(self, text_edit):
        text_edit.moveCursor(QtGui.QTextCursor.End)
        text_edit.ensureCursorVisible()
        
    def update_progress_bar(self, value):
        """Met à jour la valeur de la barre de progression."""
        self.progress_bar.setValue(value)
        
    def append_log(self, message: str, level: str = "INFO", update_progress: bool = False):
        """Ajoute du texte au log."""
        from datetime import datetime
        ts = datetime.now().strftime("[%H:%M:%S]")
        line = f"{ts} [{level.upper()}] {message}\n"
        self.txt_log.insertPlainText(line)
        if update_progress:
            current_value = self.progress_bar.value()
            if current_value < 100:
                self.progress_bar.setValue(current_value + 1)
        
    def _setup_ui(self):
        v = QtWidgets.QVBoxLayout(self)
        self.txt_log = QtWidgets.QTextEdit()
        self.txt_log.setReadOnly(True)
        # Connecter le signal textChanged pour faire défiler automatiquement vers le bas
        self.txt_log.textChanged.connect(lambda: self._scroll_to_bottom(self.txt_log))
        self.lbl_status = QtWidgets.QLabel("En attente de commande...")
        
        # Barre de progression
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        
        h = QtWidgets.QHBoxLayout()
        self.btn_stop = QtWidgets.QPushButton("Stop")
        # Connecter le clic du bouton stop à l'émission du signal stopRequested
        self.btn_stop.clicked.connect(self.stopRequested.emit)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #ff5a5a, stop: 1 #cc0000);
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                padding: 6px 12px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #ff6a6a, stop: 1 #ff1a1a);
                border: 1px solid #ff5a5a;
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #cc0000, stop: 1 #ff5a5a);
                border: 1px solid #2a2a2a;
            }
            QPushButton:disabled {
                background-color: #3a3a3a;
                color: #6a6a6a;
                border: 1px solid #2a2a2a;
            }
        """)
        h.addWidget(self.lbl_status)
        h.addStretch(1)
        h.addWidget(self.btn_stop)
        v.addWidget(self.txt_log, 1)
        v.addWidget(self.progress_bar)
        v.addLayout(h)
class InstallTabPage(TabPage):
    """Page d'onglet pour l'installation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
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
        from pathlib import Path
        default_path = str(Path.home() / "MyApp")
        content_widget.widgets['dest_path'].setText(default_path)
        
        browse_btn = QtWidgets.QPushButton("Parcourir...")
        browse_btn.clicked.connect(lambda: self._browse_destination(content_widget.widgets['dest_path']))
        
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
        image_browse_btn.clicked.connect(lambda: self._browse_wizard_image(content_widget.widgets['wizard_image']))
        
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
        scroll_area = QtWidgets.QScrollArea(self)  # Passer self comme parent
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        
        # Ajouter le scroll_area au layout de self
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        
        # Stocker content_widget.widgets et install_btn dans self pour y accéder depuis l'extérieur
        self.widgets = content_widget.widgets
        self.install_btn = content_widget.install_btn
       
    def _browse_destination(self, dest_widget):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Choisir le répertoire de destination"
        )
        if directory:
            dest_widget.setText(directory)
 
    def _browse_wizard_image(self, image_widget):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Sélectionner une image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            image_widget.setText(file_path)
       

class ProfilesTabPage(TabPage):
    """Page d'onglet pour les profils."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        v = QtWidgets.QVBoxLayout(self)
        
        self.lst_profiles = QtWidgets.QListWidget()
        
        btn_new = QtWidgets.QPushButton("Nouveau")
        btn_save = QtWidgets.QPushButton("Enregistrer")
        btn_del = QtWidgets.QPushButton("Supprimer")
        btn_export = QtWidgets.QPushButton("Exporter JSON")
        btn_import = QtWidgets.QPushButton("Importer JSON")
        
        h = QtWidgets.QHBoxLayout()
        for b in (btn_new, btn_save, btn_del, btn_export, btn_import):
            h.addWidget(b)
        h.addStretch(1)
        
        v.addWidget(self.lst_profiles)
        v.addLayout(h)
        
        # Stocker les widgets dans self pour y accéder depuis l'extérieur
        self.widgets = {
            'lst_profiles': self.lst_profiles,
            'btn_new': btn_new,
            'btn_save': btn_save,
            'btn_del': btn_del,
            'btn_export': btn_export,
            'btn_import': btn_import
        }
            
class OptionsTabPage(TabPage):
    """Page d'onglet pour les options."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        # Créer un widget pour contenir tous les éléments
        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setVerticalSpacing(12)  # Réduire l'espacement vertical entre les lignes
        
        cmb_backend = QtWidgets.QComboBox()
        cmb_backend.addItems(list(BACKENDS.keys()))
        
        chk_onefile = QtWidgets.QCheckBox("Un seul-fichier")
        chk_onefile.setChecked(True)
        chk_windowed = QtWidgets.QCheckBox("GUI / sans console")
        chk_windowed.setChecked(True)
        chk_clean = QtWidgets.QCheckBox("Nettoyage --clean")
        chk_clean.setChecked(True)
        chk_console = QtWidgets.QCheckBox("Forcer console")        
        
        # Widget pour les répertoires et fichiers à inclure avec leur contenu
        tbl_dirs_to_include = AddFilesAndDirectoriesWidget()
        
        ed_hidden = QtWidgets.QPlainTextEdit()
        ed_hidden.setPlaceholderText("module_a\npackage_b.sousmodule\n...")
        
        ed_extra = QtWidgets.QPlainTextEdit()
        ed_extra.setPlaceholderText("Args supplémentaires ligne par ligne, ex: \n--exclude-module some_heavy_pkg\n--onedir")
        
        ed_python = LabeledLineEdit("Python (optionnel)")
        ed_python.setText(detect_python_exe())
        
        # Stocker les widgets dans le widget de la page pour y accéder depuis l'extérieur
        content_widget.widgets = {
            'cmb_backend': cmb_backend,
            'chk_onefile': chk_onefile,
            'chk_windowed': chk_windowed,
            'chk_clean': chk_clean,
            'chk_console': chk_console,
            'tbl_dirs_to_include': tbl_dirs_to_include,
            'ed_hidden': ed_hidden,
            'ed_extra': ed_extra,
            'ed_python': ed_python
        }
        
        for row in [
            ("Outil", cmb_backend),
            ("Un fichier", chk_onefile),
            ("Fenêtre GUI", chk_windowed),
            ("Nettoyer", chk_clean),
            ("Console", chk_console),
            ("Fichiers/Répertoires à inclure", tbl_dirs_to_include),
            ("Hidden imports", ed_hidden),
            ("Args extra", ed_extra),
            ("Python", ed_python),
        ]:
            form.addRow(row[0], row[1])
        
        # Créer un QScrollArea et y ajouter le content_widget
        scroll_area = QtWidgets.QScrollArea(self)  # Passer self comme parent
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        
        # Ajouter le scroll_area au layout de self
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        
        # Stocker content_widget.widgets dans self pour y accéder depuis l'extérieur
        self.widgets = content_widget.widgets