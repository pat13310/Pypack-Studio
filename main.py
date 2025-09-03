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

APP_NAME = "PyPack Studio v1.3"

# Importer le style personnalisé depuis le fichier styles.py
from src.styles import CUSTOM_STYLE

# en haut de ton fichier pypack_studio.py
from src.services.profile_manager import ProfileManager
from src.services.log_service import LogService
from src.services.file_manager import FileManagerService


class MainWindow(QtWidgets.QMainWindow):
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
    def reset_ui_fields(self):
        # Onglet Projet
        self.page_project.ed_project.setText("")
        self.page_project.ed_entry.setText("")
        self.page_project.ed_name.setText("")
        self.page_project.ed_icon.setText("")
        self.page_project.ed_output.setText("")
        self.page_project.chk_open_output_dir.setChecked(True)
        self.page_project.chk_create_setup.setChecked(False)
        # Onglet Options
        self.page_options.widgets['cmb_backend'].setCurrentIndex(0)
        self.page_options.widgets['chk_onefile'].setChecked(True)
        self.page_options.widgets['chk_windowed'].setChecked(True)
        self.page_options.widgets['chk_clean'].setChecked(True)
        self.page_options.widgets['chk_console'].setChecked(False)
        self.page_options.widgets['tbl_directories'].setValue([])
        self.page_options.widgets['tbl_dirs_to_include'].setValue([])
        self.page_options.widgets['ed_hidden'].setPlainText("")
        self.page_options.widgets['ed_extra'].setPlainText("")
        self.page_options.widgets['ed_python'].setText("")
    
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

        self.pages = QtWidgets.QStackedWidget()

        self.page_project = ProjectTabPage()
        self.page_project.setupCheckChanged.connect(self._update_install_tab_visibility)
        self.page_project.btn_analyze.clicked.connect(lambda: self._analyze_project())
        self.page_project.btn_build.clicked.connect(lambda: self._on_build_clicked())
        self.page_project.btn_clean.clicked.connect(lambda: self._clean_output())
        self.page_options = OptionsTabPage()
        self.page_profiles = ProfilesTabPage()
        self.page_install = InstallTabPage()
        self.page_install.install_btn.clicked.connect(lambda: InstallAppAction(self).execute())
        self.page_output = OutputTabPage()

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
        self.nav.setCurrentRow(0)

        # Définir l'icône de la fenêtre
        window_icon_path = "res/pypack.ico"
        if not os.path.exists(window_icon_path):
            window_icon_path = "res/pypack.png"
        if os.path.exists(window_icon_path):
            self.setWindowIcon(QtGui.QIcon(window_icon_path))
        # Définir l'icône de la fenêtre
        window_icon_path = "res/pypack.ico"
        if not os.path.exists(window_icon_path):
            window_icon_path = "res/pypack.png"
        if os.path.exists(window_icon_path):
            self.setWindowIcon(QtGui.QIcon(window_icon_path))

        
    # ---------------- Logic ----------------
    def _switch_page(self, idx: int):
        # Sauvegarder le profil actif à chaque changement d'onglet
        active_profile_name = self.settings.value("active_profile", "")
        if active_profile_name and active_profile_name != "default":
            try:
                cfg = self._config_from_ui()
                self.profile_mgr.save(active_profile_name, cfg)
            except Exception as e:
                print(f"Erreur lors de la sauvegarde du profil actif '{active_profile_name}' (changement d'onglet): {e}")
        self.pages.setCurrentIndex(idx)
    
    
    def _toggle_tab_visibility(self, tab_index, state, checked_value=None, fallback_index=0):
        """Affiche ou masque un onglet en fonction de l'état de la checkbox associée."""
        # state est maintenant un entier (0 ou 2)
        is_visible = (state == 2)
        print(f"[DEBUG] main tab_index={tab_index}, state={state}, is_visible={is_visible}")
        self.nav.setRowHidden(tab_index, not is_visible)
        if not is_visible and self.nav.currentRow() == tab_index:
            self.nav.setCurrentRow(fallback_index)
        
    def _update_install_tab_visibility(self, state):
        self._toggle_tab_visibility(self.install_tab_index, state)
        
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
            create_setup=self.page_project.chk_create_setup.isChecked(),
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
        self.page_project.chk_create_setup.setChecked(bool(getattr(cfg, 'create_setup', False)))
        # Correction : garantir la présence des champs et le bon format
        directories = getattr(cfg, 'directories_to_create', [])
        if directories is None:
            directories = []
        dirs_to_include = getattr(cfg, 'dirs_to_include', [])
        if dirs_to_include is None:
            dirs_to_include = []
        self.page_options.widgets['tbl_dirs_to_include'].setValue(getattr(cfg, 'dirs_to_include', []))
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
        from src.profile_list_utils import update_profiles_list_widget
        profiles = self.profile_mgr.load_all().keys()
        active_profile = self.settings.value("active_profile", "")
        update_profiles_list_widget(self.page_profiles.widgets['lst_profiles'], profiles, active_profile)
        # Sélectionne l'item actif pour garder le style sélectionné
        for i in range(self.page_profiles.widgets['lst_profiles'].count()):
            item = self.page_profiles.widgets['lst_profiles'].item(i)
            if item.text() == active_profile:
                self.page_profiles.widgets['lst_profiles'].setCurrentItem(item)
                break

    def _on_profile_selected(self):
        item = self.page_profiles.widgets['lst_profiles'].currentItem()
        if not item:
            self.setWindowTitle(APP_NAME)
            return
        profile_name = item.text()
        payload = self.profile_mgr.get(profile_name)
        if payload:
            cfg = BuildConfig(**payload).normalized()
            self._apply_config_to_ui(cfg)
            # Met à jour explicitement la case à cocher selon le profil chargé
            self.page_project.chk_create_setup.setChecked(bool(getattr(cfg, 'create_setup', False)))
            # Synchronise la visibilité de l’onglet Installation
            state_enum = self.page_project.chk_create_setup.checkState()
            state_int = state_enum.value if hasattr(state_enum, 'value') else int(state_enum)
            print(f"check {state_int}")
            self._update_install_tab_visibility(state_int)
            # Sauvegarder le nom du profil actif dans les settings
            self.settings.setValue("active_profile", profile_name)
            # Mettre à jour la barre de titre avec le profil actif
            self.setWindowTitle(f"{APP_NAME}  [ {profile_name} ]")
        else:
            self.setWindowTitle(APP_NAME)

    def _profile_new(self):
        self.reset_ui_fields()
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
        """Charge les paramètres de l'application et restaure l'état de l'UI avec fallback hiérarchique."""
        # --- Étape 1 : Taille et position de la fenêtre ---
        self.resize(self.settings.value("win/size", QtCore.QSize(1100, 720)))
        self.move(self.settings.value("win/pos", QtCore.QPoint(100, 100)))

        # --- Étape 2 : Mise à jour de la liste des profils ---
        self._refresh_profiles_list()

        # --- Étape 3 : Charger configuration via hiérarchie ---
        loaded = (
            self._try_load_profile(self.settings.value("active_profile", "")) or
            self._try_load_profile("default") or
            self._try_load_last_config() or
            self._load_builtin_defaults()
        )

        if not loaded:
            print("[WARN] Aucun profil n'a pu être chargé, interface initialisée avec les valeurs par défaut.")

        # --- Étape 4 : Charger les options projet ---
        self._load_project_options()

        # --- Étape 5 : Mettre à jour visibilité de l'onglet Installation ---
        #self._update_install_tab_visibility(self.page_project.chk_create_setup.checkState())

# ---------------------
# Méthodes utilitaires
# ---------------------

    def _try_load_profile(self, profile_name: str) -> bool:
        """Tente de charger un profil. Retourne True si succès."""
        if not profile_name:
            return False
        profile = self.profile_mgr.get(profile_name)
        if not profile:
            print(f"[INFO] Profil '{profile_name}' introuvable.")
            return False
        try:
            cfg = BuildConfig(**profile).normalized()
            self._apply_config_to_ui(cfg)
            self._select_profile_in_list(profile_name)
            print(f"[INFO] Profil '{profile_name}' chargé avec succès.")
            return True
        except Exception as e:
            print(f"[ERROR] Échec du chargement du profil '{profile_name}': {e}")
            return False

    def _try_load_last_config(self) -> bool:
        """Tente de restaurer la dernière configuration enregistrée (last_config)."""
        last = self.settings.value("last_config", "")
        if not last:
            return False
        try:
            cfg = BuildConfig(**json.loads(last)).normalized()
            self._apply_config_to_ui(cfg)
            print("[INFO] last_config restaurée avec succès.")
            return True
        except Exception as e:
            print(f"[ERROR] Échec du chargement de last_config: {e}")
            return False

    def _load_builtin_defaults(self) -> bool:
        """Charge une configuration par défaut codée en dur (dernier niveau de fallback)."""
        try:
            default_cfg = BuildConfig(
                project_name="NouveauProjet",
                version="1.0.0",
                output_dir="./build"
            ).normalized()
            self._apply_config_to_ui(default_cfg)
            print("[INFO] Configuration par défaut appliquée (fallback).")
            return True
        except Exception as e:
            print(f"[CRITICAL] Impossible d'appliquer la configuration par défaut: {e}")
            return False

    def _select_profile_in_list(self, profile_name: str):
        """Sélectionne un profil dans la liste si trouvé."""
        items = self.page_profiles.widgets['lst_profiles'].findItems(profile_name, QtCore.Qt.MatchExactly)
        if items:
            self.page_profiles.widgets['lst_profiles'].setCurrentItem(items[0])

    def _load_project_options(self):
        """Charge les options projet depuis les QSettings."""
        self.page_project.chk_open_output_dir.setChecked(
            self.settings.value("project/open_output_dir", True, type=bool)
        )
        self.page_project.chk_create_setup.setChecked(
            self.settings.value("project/create_setup", False, type=bool)
        )


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
    app = QtWidgets.QApplication(sys.argv)
    app.setOrganizationName(APP_ORG)
    app.setApplicationName(APP_NAME)
    # Style classique propre
    app.setStyle("Fusion")
    app.setStyleSheet(CUSTOM_STYLE)
    w = MainWindow()
    
    # Centrer horizontalement et positionner à 50 pixels du haut
    screen_size = app.primaryScreen().size()
    window_width = w.width()
    x = (screen_size.width() - window_width) // 2
    w.move(x, 5)
    
    w.show()
    try:
        sys.exit(app.exec())
    except Exception as e:
        print(f"Exception in app.exec(): {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()