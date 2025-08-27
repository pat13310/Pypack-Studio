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
from src.tabpage import make_project_page, make_options_page, make_profiles_page, make_output_page, make_install_page
from src.worker import BuildWorker

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
        self.page_project = make_project_page(self)
        self.page_options = make_options_page()
        self.page_profiles = make_profiles_page()
        self.page_install = make_install_page()
        self.page_install.widget().install_btn.clicked.connect(self._install_app_from_page)
        self.page_output = make_output_page(self)
        
        # Connecter les signaux de la page des profils
        self.page_profiles.widgets['lst_profiles'].itemSelectionChanged.connect(self._on_profile_selected)
        self.page_profiles.widgets['btn_new'].clicked.connect(self._profile_new)
        self.page_profiles.widgets['btn_save'].clicked.connect(self._profile_save)
        self.page_profiles.widgets['btn_del'].clicked.connect(self._profile_delete)
        self.page_profiles.widgets['btn_export'].clicked.connect(self._profile_export)
        self.page_profiles.widgets['btn_import'].clicked.connect(self._profile_import)
        
        for p in (self.page_project, self.page_options, self.page_profiles, self.page_install, self.page_output):
            self.pages.addWidget(p)
            
        # Initialiser LogService et FileManagerService après la création de txt_log
        self.log_service = LogService(self.txt_log)  # txt_log est maintenant disponible
        self.file_mgr = FileManagerService(self.log_service)

        # ---- Layout principal
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        h = QtWidgets.QHBoxLayout(central)
        h.addWidget(self.nav)
        h.addWidget(self.pages, 1)

        self._load_settings()
        # Définir l'icône par défaut si elle n'est pas déjà définie
        if not self.ed_icon.text():
            default_icon_path = "res/pypack.ico"
            if os.path.exists(default_icon_path):
                self.ed_icon.setText(default_icon_path)
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
        widgets = self.page_install.widget().widgets
        
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
    
    def _update_progress(self, text: str):
        # Incrémenter la progression à chaque ligne de log
        current_value = self.progress_bar.value()
        if current_value < 100:
            self.progress_bar.setValue(current_value + 1)
        
        # Réinitialiser la progression si elle atteint 100%
        if self.progress_bar.value() >= 100:
            self.progress_bar.setValue(0)

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
            project_dir=self.ed_project.text(),
            entry_script=self.ed_entry.text(),
            name=self.ed_name.text(),
            icon_path=self.ed_icon.text(),
            backend=self.page_options.widget().widgets['cmb_backend'].currentText(),
            onefile=self.page_options.widget().widgets['chk_onefile'].isChecked(),
            windowed=self.page_options.widget().widgets['chk_windowed'].isChecked(),
            clean=self.page_options.widget().widgets['chk_clean'].isChecked(),
            console=self.page_options.widget().widgets['chk_console'].isChecked(),
            #add_data=self.page_options.widget().widgets['tbl_data'].value(),
            directories_to_create=self.page_options.widget().widgets['tbl_directories'].value(),
            hidden_imports=[ln.strip() for ln in self.page_options.widget().widgets['ed_hidden'].toPlainText().splitlines() if ln.strip()],
            extra_args=[ln.strip() for ln in self.page_options.widget().widgets['ed_extra'].toPlainText().splitlines() if ln.strip()],
            output_dir=self.ed_output.text(),
            python_exe=self.page_options.widget().widgets['ed_python'].text(),
        )
        # Stocker la valeur de la checkbox pour l'utiliser dans _on_build_finished
        self.open_output_dir = self.chk_open_output_dir.isChecked()
        return cfg.normalized()

    def _apply_config_to_ui(self, cfg: BuildConfig):
        self.ed_project.setText(cfg.project_dir)
        self.ed_entry.setText(cfg.entry_script)
        self.ed_name.setText(cfg.name)
        self.ed_icon.setText(cfg.icon_path)
        self.ed_output.setText(cfg.output_dir)
        self.page_options.widget().widgets['cmb_backend'].setCurrentText(cfg.backend)
        self.page_options.widget().widgets['chk_onefile'].setChecked(cfg.onefile)
        self.page_options.widget().widgets['chk_windowed'].setChecked(cfg.windowed)
        self.page_options.widget().widgets['chk_clean'].setChecked(cfg.clean)
        self.page_options.widget().widgets['chk_console'].setChecked(cfg.console)
        self.page_options.widget().widgets['tbl_data'].setValue(cfg.add_data)
        self.page_options.widget().widgets['tbl_directories'].setValue(cfg.directories_to_create)
        self.page_options.widget().widgets['ed_hidden'].setPlainText("\n".join(cfg.hidden_imports))
        self.page_options.widget().widgets['ed_extra'].setPlainText("\n".join(cfg.extra_args))
        self.page_options.widget().widgets['ed_python'].setText(cfg.python_exe)

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
        self.file_mgr.clean_output(out)
        
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
                    self.log_service._append_log(f"[CLEAN] Erreur: {e}", "error")
            self.log_service._append_log(f"[CLEAN] {out} vidé.", "info")

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
            QtWidgets.QMessageBox.warning(self, "Outil", f"Outil inconnu: {cfg.backend}")
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
        self.nav.setCurrentRow(4)  # Sélectionner l'onglet "Sortie & Logs"
        self.txt_log.clear()
        self._build_in_progress = True
        self.btn_stop.setEnabled(True)
        self._status("Construction en cours…")
        
        # Afficher la barre de progression
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = BuildWorker(cmd, workdir=workdir)
        self.worker.started.connect(lambda c: self.log_service.append("$ " + shlex.join(c)))
        self.worker.line.connect(lambda line: self.log_service.append(line))
        self.worker.line.connect(self._update_progress)  # tu peux garder ta barre de progression
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
                self.log_service._append_log(f"[DEBUG] Chemin de sortie: {cfg.output_dir}", "info")
                self.log_service._append_log(f"[DEBUG] Nombre d'éléments à copier: {len(cfg.directories_to_create)}", "info")
                for path in cfg.directories_to_create:
                    self.log_service._append_log(f"[DEBUG] Élément à copier: {path}", "info")
                    if Path(path).exists():
                        self.log_service._append_log(f"[DEBUG] L'élément existe: {path}", "info")
                    else:
                        self.log_service._append_log(f"[DEBUG] L'élément n'existe pas: {path}", "warning")
                if cfg.output_dir and cfg.directories_to_create:
                    self.file_mgr.copy_items(cfg.directories_to_create, cfg.output_dir, cfg.name)
                    self.log_service._append_log("[INFO] Répertoires et fichiers copiés dans le dossier de sortie.", "info")
                
                # Vérifier si les fichiers ont été copiés
                for path in cfg.directories_to_create:
                    src_path = Path(path)
                    if src_path.exists():
                        dst_path = Path(cfg.output_dir) / src_path.name
                        if dst_path.exists():
                            self.log_service._append_log(f"[DEBUG] Élément copié avec succès: {dst_path}", "info")
                        else:
                            self.log_service._append_log(f"[DEBUG] Élément non trouvé après copie: {dst_path}", "warning")
            except Exception as e:
                self.log_service._append_log(f"[ERROR] Erreur lors de la copie des répertoires et fichiers: {e}", "error")
        
        if code == 0:
            self._status("Construction réussie.")
            self.log_service.append("[INFO] Build terminé.", "INFO")
            # Ouvrir le dossier de sortie si l'option est activée
            if self.open_output_dir and cfg.output_dir:
                output_path = Path(cfg.output_dir)
                if output_path.exists():
                    QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(output_path)))
                    self._status("Dossier de sortie ouvert.")

        else:
            self._status(f"Construction échouée avec le code {code}.")
        self.btn_stop.setEnabled(False)
        self._build_in_progress = False
        if code == 0:
            QtWidgets.QMessageBox.information(self, "Succès", "Build terminé avec succès.")
        else:
            QtWidgets.QMessageBox.warning(self, "Échec", f"Le build a échoué (code {code}). Consultez les logs.")

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
        name, ok = QtWidgets.QInputDialog.getText(self, "Nouveau profil", "Nom du profil :")
        if not ok or not name.strip():
            return
        if self.profile_mgr.get(name):
            QtWidgets.QMessageBox.warning(self, "Profils", "Ce nom existe déjà.")
            return
        cfg = self._config_from_ui()
        self.profile_mgr.save(name, cfg)
        self._refresh_profiles_list()

    def _profile_save(self):
        item = self.page_profiles.widgets['lst_profiles'].currentItem()
        if not item:
            return
        self.profile_mgr.save(item.text(), self._config_from_ui())
        self.log_service.append(f"Profil sauvegardé: {item.text()}", "INFO")

    def _profile_delete(self):
        item = self.page_profiles.widgets['lst_profiles'].currentItem()
        if not item:
            return
        self.profile_mgr.delete(item.text())
        self._refresh_profiles_list()
        self.log_service.append(f"Profil supprimé: {item.text()}", "INFO")

    def _profile_export(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Exporter profils", filter="JSON (*.json)")
        if not path:
            return
        self.profile_mgr.export_to_file(path)
        self.log_service.append(f"Profils exportés -> {path}", "INFO")

    def _profile_import(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Importer profils", filter="JSON (*.json)")
        if not path:
            return
        try:
            self.profile_mgr.import_from_file(path)
            self._refresh_profiles_list()
            self.log_service.append(f"Profils importés depuis {path}", "INFO")
        except Exception as e:
            self.log_service.append(f"Erreur import profils: {e}", "ERROR")
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
        # Charger la valeur de la checkbox "Afficher le répertoire de sortie à la fin du build"
        open_output_dir = self.settings.value("project/open_output_dir", True, type=bool)
        self.chk_open_output_dir.setChecked(open_output_dir)
        # Charger l'onglet courant
        current_tab = self.settings.value("current_tab", 0, type=int)
        self.nav.setCurrentRow(current_tab)

    def closeEvent(self, e: QtGui.QCloseEvent):
        self.settings.setValue("win/size", self.size())
        self.settings.setValue("win/pos", self.pos())
        self.settings.setValue("last_config", json.dumps(asdict(self._config_from_ui()), ensure_ascii=False))
        # Sauvegarder la valeur de la checkbox "Afficher le répertoire de sortie à la fin du build"
        self.settings.setValue("project/open_output_dir", self.chk_open_output_dir.isChecked())
        # Sauvegarder l'onglet courant
        self.settings.setValue("current_tab", self.nav.currentRow())
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
    sys.exit(app.exec())


if __name__ == "__main__":
    main()