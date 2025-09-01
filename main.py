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
from src.action import BuildAction, CleanOutputAction, AnalyzeProjectAction, ProfileNewAction, ProfileSaveAction, ProfileDeleteAction, ProfileExportAction, ProfileImportAction, InstallAppAction, CreateSetupExeAction, FileAction

APP_NAME = "PyPack Studio v1.1"

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
        #self.resize(1100, 500)
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
        self.create_setup_action = CreateSetupExeAction(self.page_output)        
        self.create_setup_action.finishRequested.connect(self.finish_setup_exe)
         
        # Connecter le signal finishRequested de BuildAction à la finish_build_app
        self.build_action.finishRequested.connect(self.finish_build_app)
         
        # Connecter le signal stopRequested de la page de sortie à la méthode stop_build
        self.page_output.stopRequested.connect(self.stop_build)
        
    def _set_nav_icons(self):
        """Définit les icônes pour les éléments de navigation."""
        icon_files = [
            ("res/projet.png", 0),
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
            dirs_to_include=self.page_options.widgets['tbl_dirs_to_include'].value(),
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
        # Correction : garantir la présence des champs et le bon format
        directories = getattr(cfg, 'directories_to_create', [])
        if directories is None:
            directories = []
        dirs_to_include = getattr(cfg, 'dirs_to_include', [])
        if dirs_to_include is None:
            dirs_to_include = []
        print(f"Application de la config à l'UI: dirs_to_include = {dirs_to_include}")  # Debug
        self.page_options.widgets['tbl_dirs_to_include'].setValue(dirs_to_include)
        self.page_options.widgets['ed_hidden'].setPlainText("\n".join(getattr(cfg, 'hidden_imports', [])))
        self.page_options.widgets['ed_extra'].setPlainText("\n".join(getattr(cfg, 'extra_args', [])))
        self.page_options.widgets['ed_python'].setText(getattr(cfg, 'python_exe', ""))

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
        
    def finish_build_app(self):
        # Créer l'environnment pour l'executabla de l'application
        cfg = self._config_from_ui()
        
        # On deplace dans le rep res le dossier application        
        source_path = Path(cfg.output_dir) / f"{cfg.name}.exe"
        dest_path = Path(cfg.output_dir)  / cfg.name/ f"{cfg.name}.exe"
        FileAction(self).execute(str(source_path), str(dest_path))
        
        # On deplace dans le rep application le dossier application
        source_internal = Path(cfg.output_dir) / "_internal"
        dest_internal = Path(cfg.output_dir)  / cfg.name/ "_internal"
        FileAction(self).execute(str(source_internal), str(dest_internal))
        
        # Vérifier si l'option "Créer un setup après le build" est cochée
        if hasattr(self, 'page_project') and self.page_project.chk_create_setup.isChecked():
            
            self.create_setup_action.execute()
        else:
            print("Option 'Créer un setup après le build' non cochée, skipping setup creation")
        
    
    def finish_setup_exe(self):
        """Termine la configuration de setup.exe en déplaçant les fichiers nécessaires."""
        # Utiliser MoveFileAction pour effectuer des opérations de déplacement supplémentaires
        # Par exemple, s'assurer que setup.exe est bien dans le répertoire de l'application
        # Récupérer la configuration actuelle
        cfg = self._config_from_ui()
        
        # Définir les chemins source et destination
        # setup.exe est normalement déjà créé dans dist_setup/setup.exe
        # et déplacé vers cfg.output_dir/cfg.name/setup.exe
        source_path = Path(cfg.output_dir) / "setup.exe"
        # On peut par exemple le déplacer à la racine du répertoire de sortie
        dest_path = Path(cfg.output_dir)  / cfg.name/ "setup.exe"
        
        # Vérifier si le fichier source existe
        if source_path.exists():
            # Utiliser MoveFileAction pour déplacer le fichier
            move_action = FileAction(self)
            move_action.execute(str(source_path), str(dest_path))
        else:
            # Afficher un message d'information si le fichier n'existe pas
            QtWidgets.QMessageBox.information(
                self,
                "Information",
                f"Le fichier setup.exe n'a pas été trouvé à l'emplacement attendu: {source_path}"
            )
            # Ajouter un log
            self.log_service.append(f"[FINISH] Fichier setup.exe non trouvé: {source_path}", "WARNING")
    
    # --- Profils ---
    def _refresh_profiles_list(self):
        self.page_profiles.widgets['lst_profiles'].clear()
        for name in sorted(self.profile_mgr.load_all().keys()):
            self.page_profiles.widgets['lst_profiles'].addItem(name)

    def _on_profile_selected(self):
        item = self.page_profiles.widgets['lst_profiles'].currentItem()
        if not item:
            return
        profile_name = item.text()
        payload = self.profile_mgr.get(profile_name)
        if payload:
            cfg = BuildConfig(**payload).normalized()
            print(f"Chargement du profil '{profile_name}': dirs_to_include = {cfg.dirs_to_include}")  # Debug
            self._apply_config_to_ui(cfg)
            # Sauvegarder le nom du profil actif dans les settings
            self.settings.setValue("active_profile", profile_name)

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
        # Charger le profil actif s'il existe et s'il n'est pas "default"
        active_profile_name = self.settings.value("active_profile", "")
        if active_profile_name and active_profile_name != "default":
            active_profile = self.profile_mgr.get(active_profile_name)
            if active_profile:
                try:
                    cfg = BuildConfig(**active_profile).normalized()
                    self._apply_config_to_ui(cfg)
                    # Sélectionner le profil actif dans la liste
                    items = self.page_profiles.widgets['lst_profiles'].findItems(active_profile_name, QtCore.Qt.MatchExactly)
                    if items:
                        self.page_profiles.widgets['lst_profiles'].setCurrentItem(items[0])
                    return  # On a chargé le profil actif, on sort de la méthode
                except Exception as e:
                    print(f"Erreur lors du chargement du profil actif '{active_profile_name}': {e}")
        
        # Si aucun profil actif n'a été chargé, charger le profil "default" s'il existe, sinon charger last_config
        default_profile = self.profile_mgr.get("default")
        if default_profile:
            try:
                cfg = BuildConfig(**default_profile).normalized()
                self._apply_config_to_ui(cfg)
                # Sélectionner le profil "default" dans la liste
                items = self.page_profiles.widgets['lst_profiles'].findItems("default", QtCore.Qt.MatchExactly)
                if items:
                    self.page_profiles.widgets['lst_profiles'].setCurrentItem(items[0])
            except Exception as e:
                print(f"Erreur lors du chargement du profil 'default': {e}")
                # En cas d'erreur, charger last_config comme fallback
                last = self.settings.value("last_config", "")
                if last:
                    try:
                        cfg = BuildConfig(**json.loads(last)).normalized()
                        self._apply_config_to_ui(cfg)
                    except Exception:
                        pass
        else:
            # Si aucun profil "default" n'existe, charger last_config
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
        # Sauvegarder la configuration actuelle dans le profil actif s'il y en a un
        active_profile_name = self.settings.value("active_profile", "")
        if active_profile_name and active_profile_name != "default":
            try:
                cfg = self._config_from_ui()
                self.profile_mgr.save(active_profile_name, cfg)
            except Exception as e:
                print(f"Erreur lors de la sauvegarde du profil actif '{active_profile_name}': {e}")
        
        # Sauvegarder la configuration actuelle dans le profil "default" comme fallback
        try:
            cfg = self._config_from_ui()
            self.profile_mgr.save("default", cfg)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du profil 'default': {e}")
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