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
from src.backends import BuildConfig, normpath,   APP_ORG ,BACKENDS
from src.tabpage import make_project_page, OutputTabPage, InstallTabPage, ProfilesTabPage, OptionsTabPage, ProjectTabPage
from src.worker import BuildWorker
from src.action import BuildAction, CleanOutputAction, AnalyzeProjectAction, ProfileNewAction, ProfileSaveAction, ProfileDeleteAction, ProfileExportAction, ProfileImportAction, InstallAppAction, StopBuildAction

APP_NAME = "PyPack Studio"

# Importer le style personnalisé depuis le fichier styles.py
from src.styles import CUSTOM_STYLE

# en haut de ton fichier pypack_studio.py
from src.services.profile_manager import ProfileManager
from src.services.log_service import LogService
from src.services.file_manager import FileManagerService


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1100, 500)
        self.setFixedSize(1100, 820)
        self.settings = QtCore.QSettings(APP_ORG, APP_NAME)
        self.profile_mgr = ProfileManager(self.settings)
        self._build_in_progress = False

        # ---- Barre latérale
        self.nav = QtWidgets.QListWidget()
        self.nav.setObjectName("nav")
        self.nav.addItems(["Projet", "Options", "Profils","Installation", "Sortie & Logs"])
        self.nav.setSpacing(10)
        self.nav.setIconSize(QtCore.QSize(50, 50))  # Agrandir les icônes
        self.nav.currentRowChanged.connect(self._switch_page)
        
        # Ajout des icônes aux onglets
        # Premier onglet "Projet" avec projet.png
        if os.path.exists("./res/projet.png"):
            icon_projet = QtGui.QIcon("./res/projet.png")
            self.nav.item(0).setIcon(icon_projet)
        
        # Deuxième onglet "Options" avec pngegg.png
        if os.path.exists("res/option.png"):
            icon_options = QtGui.QIcon("res/option.png")
            self.nav.item(1).setIcon(icon_options)

        # Triosième onglet "Profile" avec profile.png
        if os.path.exists("res/profile.png"):
            icon_profile = QtGui.QIcon("res/profile.png")
            self.nav.item(2).setIcon(icon_profile)
        
        
        # Quatrième onglet "Installation" avec installation.png
        if os.path.exists("res/installation.png"):
            icon_install = QtGui.QIcon("res/installation.png")
            self.nav.item(3).setIcon(icon_install)
        
        # Cinquième onglet "Logs" avec log.png
        if os.path.exists("res/log.png"):
            icon_log = QtGui.QIcon("res/log.png")
            self.nav.item(4).setIcon(icon_log)
                
        # ---- Pages
        self.pages = QtWidgets.QStackedWidget()
        self.page_project = ProjectTabPage()
        self.page_project.btn_analyze.clicked.connect(lambda: self._analyze_project())
        self.page_project.btn_build.clicked.connect(lambda: self._on_build_clicked())
        self.page_project.btn_clean.clicked.connect(lambda: self._clean_output())
        self.page_options = OptionsTabPage()
        self.page_profiles = ProfilesTabPage()
        self.page_install = InstallTabPage()
        self.page_install.install_btn.clicked.connect(lambda: InstallAppAction(self).execute())
        self.page_output = OutputTabPage()
        
        # Connecter les signaux de la page des profils
        self.page_profiles.widgets['lst_profiles'].itemSelectionChanged.connect(self._on_profile_selected)
        self.page_profiles.widgets['btn_new'].clicked.connect(lambda: ProfileNewAction(self).execute())
        self.page_profiles.widgets['btn_save'].clicked.connect(lambda: ProfileSaveAction(self).execute())
        self.page_profiles.widgets['btn_del'].clicked.connect(lambda: ProfileDeleteAction(self).execute())
        self.page_profiles.widgets['btn_export'].clicked.connect(lambda: ProfileExportAction(self).execute())
        self.page_profiles.widgets['btn_import'].clicked.connect(lambda: ProfileImportAction(self).execute())
        
        for p in (self.page_project, self.page_options, self.page_profiles, self.page_install, self.page_output):
            self.pages.addWidget(p)
            
        # Initialiser LogService et FileManagerService après la création de txt_log
        self.log_service = LogService(self.page_output.txt_log)  # txt_log est maintenant dans la page de log
        self.file_mgr = FileManagerService(self.log_service)

        # ---- Layout principal
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        h = QtWidgets.QHBoxLayout(central)
        h.addWidget(self.nav)
        h.addWidget(self.pages, 1)

        self._load_settings()
        # Définir l'icône par défaut si elle n'est pas déjà définie
        if not self.page_project.ed_icon.text():
            default_icon_path = "res/pypack.ico"
            if os.path.exists(default_icon_path):
                self.page_project.ed_icon.setText(default_icon_path)
        self.nav.setCurrentRow(0)

        # Définir l'icône de la fenêtre
        window_icon_path = "res/pypack.ico"
        if not os.path.exists(window_icon_path):
            window_icon_path = "res/pypack.png"
        if os.path.exists(window_icon_path):
            self.setWindowIcon(QtGui.QIcon(window_icon_path))

    # ---------------- Pages ----------------
    def _browse_destination(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choisir le répertoire de destination"
        )
        if directory:
            self.ed_dest_path.setText(directory)
            
    def _browse_wizard_image(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Sélectionner une image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.ed_wizard_image.setText(file_path)
            
    def _install_app(self):
        # Cette méthode n'est plus utilisée directement, mais conservée pour compatibilité
        pass
    
    def _install_app_from_page(self):
        # Récupérer les valeurs des widgets de la page d'installation
        widgets = self.page_install.widgets
        
        app_name = widgets['app_name'].text() or "MyApp"
        dest_path = widgets['dest_path'].text()
        wizard_image = widgets['wizard_image'].text()
        
        # Vérifier que le chemin de destination n'est pas vide
        if not dest_path:
            QtWidgets.QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un dossier de destination.")
            return
            
        # Importer l'assistant d'installation
        from src.install_wizard import InstallWizard, WizardConfig
        
        # Créer la configuration du wizard
        config = WizardConfig(
            app_name=app_name,
            dest_path=dest_path,
            wizard_image=wizard_image
        )
        
        # Mettre à jour les textes personnalisés si ils sont saisis
        if widgets['intro_title'].text():
            config.intro_title = widgets['intro_title'].text()
        if widgets['intro_subtitle'].text():
            config.intro_subtitle = widgets['intro_subtitle'].text()
        if widgets['intro_text'].toPlainText():
            config.intro_text = widgets['intro_text'].toPlainText()
            
        if widgets['app_info_title'].text():
            config.app_info_title = widgets['app_info_title'].text()
        if widgets['app_info_subtitle'].text():
            config.app_info_subtitle = widgets['app_info_subtitle'].text()
            
        if widgets['components_title'].text():
            config.components_title = widgets['components_title'].text()
        if widgets['components_subtitle'].text():
            config.components_subtitle = widgets['components_subtitle'].text()
            
        if widgets['install_options_title'].text():
            config.install_options_title = widgets['install_options_title'].text()
        if widgets['install_options_subtitle'].text():
            config.install_options_subtitle = widgets['install_options_subtitle'].text()
            
        if widgets['destination_title'].text():
            config.destination_title = widgets['destination_title'].text()
        if widgets['destination_subtitle'].text():
            config.destination_subtitle = widgets['destination_subtitle'].text()
            
        if widgets['summary_title'].text():
            config.summary_title = widgets['summary_title'].text()
        if widgets['summary_subtitle'].text():
            config.summary_subtitle = widgets['summary_subtitle'].text()
        
        # Créer et afficher l'assistant d'installation avec la configuration
        wizard = InstallWizard(config=config)
        
        # Afficher l'assistant
        wizard.exec()
            
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
    
    def copy_files_and_directories_to_output(self, directories_to_create: List[str], output_dir: str, name: str):
        """
        Copie les fichiers et répertoires spécifiés vers le dossier de sortie.
        
        Args:
            directories_to_create: Liste des chemins des fichiers/répertoires à copier
            output_dir: Chemin du dossier de sortie
            name: Nom de l'application (utilisé pour déterminer le sous-dossier dans dist/)
        """
        import shutil
        from pathlib import Path
        
        output_path = Path(output_dir)
        
        # S'assurer que le dossier de sortie existe
        output_path.mkdir(parents=True, exist_ok=True)
        
        for path_str in directories_to_create:
            if not path_str.strip():
                continue
                
            src_path = Path(path_str)
            if not src_path.exists():
                self.log_service._append_log(f"[WARNING] Le chemin spécifié n'existe pas: {path_str}", "warning")
                continue
                
            try:
                # Déterminer le chemin de destination
                # Si le output_dir se termine par le nom de l'application, on copie directement dedans
                # Sinon, on crée un sous-dossier avec le nom de l'application
                if output_path.name == name:
                    app_output_path = output_path
                else:
                    app_output_path = output_path / name
                    app_output_path.mkdir(parents=True, exist_ok=True)
                
                # Si le fichier est un PNG, le copier dans un sous-dossier res
                if src_path.is_file() and src_path.suffix.lower() == '.png':
                    res_dir = app_output_path / 'res'
                    res_dir.mkdir(parents=True, exist_ok=True)
                    dst_path = res_dir / src_path.name
                else:
                    dst_path = app_output_path / src_path.name
                
                # Copier le fichier ou le répertoire
                if src_path.is_file():
                    shutil.copy2(src_path, dst_path)
                    self.log_service._append_log(f"[INFO] Fichier copié: {src_path} -> {dst_path}", "info")
                elif src_path.is_dir():
                    # Pour les répertoires, on utilise copytree avec dirs_exist_ok=True
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                    self.log_service._append_log(f"[INFO] Répertoire copié: {src_path} -> {dst_path}", "info")
                    
            except Exception as e:
                self.log_service._append_log(f"[ERROR] Erreur lors de la copie de {path_str}: {str(e)}", "error")

    def _config_from_ui(self) -> BuildConfig:
        cfg = BuildConfig(
            project_dir=self.page_project.ed_project.text(),
            entry_script=self.page_project.ed_entry.text(),
            name=self.page_project.ed_name.text(),
            icon_path=self.page_project.ed_icon.text(),
            backend=self.page_options.widgets['cmb_backend'].currentText(),
            onefile=self.page_options.widgets['chk_onefile'].isChecked(),
            windowed=self.page_options.widgets['chk_windowed'].isChecked(),
            clean=self.page_options.widgets['chk_clean'].isChecked(),
            console=self.page_options.widgets['chk_console'].isChecked(),
            #add_data=self.page_options.widgets['tbl_data'].value(),
            directories_to_create=self.page_options.widgets['tbl_directories'].value(),
            hidden_imports=[ln.strip() for ln in self.page_options.widgets['ed_hidden'].toPlainText().splitlines() if ln.strip()],
            extra_args=[ln.strip() for ln in self.page_options.widgets['ed_extra'].toPlainText().splitlines() if ln.strip()],
            output_dir=self.page_project.ed_output.text(),
            python_exe=self.page_options.widgets['ed_python'].text(),
        )
        # Stocker la valeur de la checkbox pour l'utiliser dans _on_build_finished
        self.open_output_dir = self.page_project.chk_open_output_dir.isChecked()
        return cfg.normalized()

    def _apply_config_to_ui(self, cfg: BuildConfig):
        self.page_project.ed_project.setText(cfg.project_dir)
        self.page_project.ed_entry.setText(cfg.entry_script)
        self.page_project.ed_name.setText(cfg.name)
        self.page_project.ed_icon.setText(cfg.icon_path)
        self.page_project.ed_output.setText(cfg.output_dir)
        self.page_options.widgets['cmb_backend'].setCurrentText(cfg.backend)
        self.page_options.widgets['chk_onefile'].setChecked(cfg.onefile)
        self.page_options.widgets['chk_windowed'].setChecked(cfg.windowed)
        self.page_options.widgets['chk_clean'].setChecked(cfg.clean)
        self.page_options.widgets['chk_console'].setChecked(cfg.console)
        self.page_options.widgets['tbl_data'].setValue(cfg.add_data)
        self.page_options.widgets['tbl_directories'].setValue(cfg.directories_to_create)
        self.page_options.widgets['ed_hidden'].setPlainText("\n".join(cfg.hidden_imports))
        self.page_options.widgets['ed_extra'].setPlainText("\n".join(cfg.extra_args))
        self.page_options.widgets['ed_python'].setText(cfg.python_exe)

    # --- Analyse/Nettoyage ---
    def _analyze_project(self):
        AnalyzeProjectAction(self).execute()

    def _clean_output(self):
        CleanOutputAction(self).execute()

    # --- Build ---
    def _on_build_clicked(self):
        BuildAction(self.page_output).execute(self)

    # --- Profils ---
    def _refresh_profiles_list(self):
        self.page_profiles.widgets['lst_profiles'].clear()
        for name in sorted(self.profile_mgr.load_all().keys()):
            self.page_profiles.widgets['lst_profiles'].addItem(name)

    def _on_profile_selected(self):
        item = self.page_profiles.widgets['lst_profiles'].currentItem()
        if not item:
            return
        payload = self.profile_mgr.get(item.text())
        if payload:
            cfg = BuildConfig(**payload).normalized()
            self._apply_config_to_ui(cfg)

    def _profile_new(self):
        ProfileNewAction(self).execute()

    def _profile_save(self):
        ProfileSaveAction(self).execute()

    def _profile_delete(self):
        ProfileDeleteAction(self).execute()

    def _profile_export(self):
        ProfileExportAction(self).execute()

    def _profile_import(self):
        ProfileImportAction(self).execute()

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
        # Charger la valeur de la checkbox "Afficher le répertoire de sortie à la fin du build"
        open_output_dir = self.settings.value("project/open_output_dir", True, type=bool)
        self.page_project.chk_open_output_dir.setChecked(open_output_dir)
        # Charger l'onglet courant
        current_tab = self.settings.value("current_tab", 0, type=int)
        self.nav.setCurrentRow(current_tab)

    def closeEvent(self, e: QtGui.QCloseEvent):
        self.settings.setValue("win/size", self.size())
        self.settings.setValue("win/pos", self.pos())
        self.settings.setValue("last_config", json.dumps(asdict(self._config_from_ui()), ensure_ascii=False))
        # Sauvegarder la valeur de la checkbox "Afficher le répertoire de sortie à la fin du build"
        self.settings.setValue("project/open_output_dir", self.page_project.chk_open_output_dir.isChecked())
        # Sauvegarder l'onglet courant
        self.settings.setValue("current_tab", self.nav.currentRow())
        super().closeEvent(e)


def main():
    print("Creating QApplication")  # Débogage
    app = QtWidgets.QApplication(sys.argv)
    print("QApplication created")  # Débogage
    app.setOrganizationName(APP_ORG)
    app.setApplicationName(APP_NAME)
    # Style classique propre
    app.setStyle("Fusion")
    app.setStyleSheet(CUSTOM_STYLE)
    print("Creating MainWindow")  # Débogage
    w = MainWindow()
    print("MainWindow created")  # Débogage
    
    # Centrer horizontalement et positionner à 50 pixels du haut
    screen_size = app.primaryScreen().size()
    window_width = w.width()
    x = (screen_size.width() - window_width) // 2
    w.move(x, 5)
    
    print("Showing MainWindow")  # Débogage
    w.show()
    print("MainWindow shown")  # Débogage
    print("Starting app.exec()")  # Débogage
    try:
        sys.exit(app.exec())
    except Exception as e:
        print(f"Exception in app.exec(): {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()