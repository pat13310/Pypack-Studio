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
import sys
from dataclasses import  asdict
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
from src.backends import BuildConfig,   APP_ORG 
from src.tabpage import  OutputTabPage, InstallTabPage, ProfilesTabPage, OptionsTabPage, ProjectTabPage
from src.action import BuildAction, CleanOutputAction, AnalyzeProjectAction, ProfileNewAction, ProfileSaveAction, ProfileDeleteAction, ProfileExportAction, ProfileImportAction, InstallAppAction, CreateSetupExeAction

APP_NAME = "PyPack Studio v0.9"

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
        
        # Stocker l'index de l'onglet Installation pour pouvoir le masquer/afficher
        self.install_tab_index = 3
         
        # Ajout des icônes aux onglets
        self._set_nav_icons()
        self.build_action=BuildAction(self.page_output)
         
        # Connecter le signal setupCreationRequested de BuildAction à la méthode create_setup_exe
        self.build_action.setupCreationRequested.connect(self.create_setup_exe)
         
        # Connecter le signal stopRequested de la page de sortie à la méthode stop_build
        self.page_output.stopRequested.connect(self.stop_build)
        
    def _set_nav_icons(self):
        """Définit les icônes pour les éléments de navigation."""
        icon_files = [
            ("./res/projet.png", 0),
            ("res/option.png", 1),
            ("res/profile.png", 2),
            ("res/installation.png", 3),
            ("res/log.png", 4),
        ]
        for file_path, index in icon_files:
            if os.path.exists(file_path):
                icon = QtGui.QIcon(file_path)
                self.nav.item(index).setIcon(icon)
                
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

            
    # ---------------- Logic ----------------
    def _switch_page(self, idx: int):
        self.pages.setCurrentIndex(idx)
        
    def _update_install_tab_visibility(self, state):
        """Met à jour la visibilité de l'onglet Installation en fonction de la case à cocher."""
        # Masquer ou afficher l'onglet Installation
        is_visible = state == 2  # QtCore.Qt.Checked = 2
        self.nav.setRowHidden(self.install_tab_index, not is_visible)
        
        # Si l'onglet Installation est actuellement sélectionné et qu'on le masque, basculer vers l'onglet Projet
        if not is_visible and self.nav.currentRow() == self.install_tab_index:
            self.nav.setCurrentRow(0)
        
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
        self.build_action.execute(self)
        
    def stop_build(self):
        """Arrête le processus de build en cours."""
        if self.build_action.stop():
            self.page_output.lbl_status.setText("Arrêt du build demandé...")
            self.page_output.btn_stop.setEnabled(False)
        else:
            # Optionnel: afficher un message si aucun build n'est en cours
            # QtWidgets.QMessageBox.information(self, "Stop", "Aucun build en cours.")
            pass

    def create_setup_exe(self):
        """Crée l'exécutable setup.exe."""
        # Créer et exécuter l'action de création du setup
        create_setup_action = CreateSetupExeAction(self.page_output)
        create_setup_action.execute()

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
        
        # Charger la valeur de la checkbox "Créer un setup après le build"
        create_setup = self.settings.value("project/create_setup", False, type=bool)
        self.page_project.chk_create_setup.setChecked(create_setup)
        
        # Initialiser l'état de visibilité des onglets
        # Masquer l'onglet Installation si la case à cocher n'est pas cochée
        self.nav.setRowHidden(self.install_tab_index, not create_setup)
        
        # Connecter la case à cocher à la méthode de mise à jour de la visibilité de l'onglet Installation
        # après avoir défini l'état initial
        self.page_project.chk_create_setup.stateChanged.connect(self._update_install_tab_visibility)
        
        # Charger l'onglet courant
        current_tab = self.settings.value("current_tab", 0, type=int)
        self.nav.setCurrentRow(current_tab)

    def closeEvent(self, e: QtGui.QCloseEvent):
        self.settings.setValue("win/size", self.size())
        self.settings.setValue("win/pos", self.pos())
        self.settings.setValue("last_config", json.dumps(asdict(self._config_from_ui()), ensure_ascii=False))
        # Sauvegarder la valeur de la checkbox "Afficher le répertoire de sortie à la fin du build"
        self.settings.setValue("project/open_output_dir", self.page_project.chk_open_output_dir.isChecked())
        # Sauvegarder la valeur de la checkbox "Créer un setup après le build"
        self.settings.setValue("project/create_setup", self.page_project.chk_create_setup.isChecked())
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