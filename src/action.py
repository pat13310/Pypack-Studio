"""
Fichier contenant les classes d'actions pour l'application PyPack Studio.
"""

from abc import ABC, abstractmethod
from pathlib import Path
import json
from typing import List, Tuple
from PySide6 import QtWidgets, QtCore, QtGui
from src.backends import BuildConfig, BACKENDS
from src.worker import BuildWorker
import shlex

# Créer une métaclasse personnalisée pour résoudre le conflit de métaclasse
class ActionMeta(type(QtCore.QObject), type(ABC)):
    pass


class Action(ABC, metaclass=ActionMeta):
    """Classe de base abstraite pour toutes les actions de l'application."""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    @abstractmethod
    def execute(self):
        """Exécute l'action."""
        pass


class BaseBuildAction(Action, QtCore.QObject):
    """Classe de base pour les actions de build."""
    
    def __init__(self, log_page):
        Action.__init__(self, log_page)  # Initialiser Action
        QtCore.QObject.__init__(self)  # Initialiser QObject
        self.log_page = log_page  # Stocker la page de log pour les utiliser dans d'autres méthodes
        
    def _setup_ui_for_build(self, main_window, status_text):
        """Configure l'interface utilisateur pour le build."""
        main_window.pages.setCurrentWidget(main_window.page_output)
        main_window.nav.setCurrentRow(4)  # Sélectionner l'onglet "Sortie & Logs"
        self.log_page.txt_log.clear()
        self.log_page.lbl_status.setText(status_text)
        self.log_page.btn_stop.setEnabled(False) # Désactiver le bouton stop pour cette action simple
        self.log_page.progress_bar.setVisible(True)
        self.log_page.progress_bar.setRange(0, 0) # Barre de progression indéterminée
        self.log_page.progress_bar.setValue(0)
        
        QtWidgets.QApplication.processEvents() # Forcer la mise à jour de l'UI


class BuildAction(BaseBuildAction):
    """Action pour construire l'application."""
    
    # Définir le signal personnalisé
    setupCreationRequested = QtCore.Signal()
    finishRequested = QtCore.Signal()
    
    def __init__(self, log_page):
        super().__init__(log_page)  # Initialiser BaseBuildAction
        self.line_count = 0  # Compteur de lignes pour limiter les mises à jour de la progressBar
        self.pending_progress_update = False  # Indique si une mise à jour de la progressBar est en attente
        self.worker = None  # Stocker le worker ici aussi pour y accéder via une propriété
        # Initialiser le timer pour les mises à jour de l'UI
        self.progress_timer = QtCore.QTimer()
        self.progress_timer.timeout.connect(self._update_progress_ui)
    
    @property
    def current_worker(self):
        """Retourne le worker actuellement en cours d'exécution, ou None s'il n'y en a pas."""
        return self.worker
    
    def stop(self):
        """
        Arrête le processus de build en cours.
        
        Returns:
            bool: True si un worker a été trouvé et l'arrêt a été demandé, False sinon.
        """
        if self.worker is not None:
            print(f"BuildAction.stop: Stopping worker {self.worker}") # Debug log
            self.worker.kill()
            return True
        else:
            print("BuildAction.stop: No worker to stop") # Debug log
            return False
        
    def execute(self, main_window: QtWidgets.QMainWindow):
        log_page = self.main_window  # log_page est stocké dans self.main_window
        self.main_window_ref = main_window  # Stocker main_window comme attribut
         
        if hasattr(main_window, '_build_in_progress') and main_window._build_in_progress:
            QtWidgets.QMessageBox.information(main_window, "Build", "Un build est déjà en cours.")
            return
             
        cfg = main_window._config_from_ui()
        ok, msg = cfg.validate()
        if not ok:
            QtWidgets.QMessageBox.warning(main_window, "Validation", msg)
            main_window.nav.setCurrentRow(0)
            return
             
        backend = BACKENDS.get(cfg.backend)
        if backend is None:
            QtWidgets.QMessageBox.warning(main_window, "Outil", f"Outil inconnu: {cfg.backend}")
            return
             
        cmd = backend.build_command(cfg)
        # Vérif exe disponible
        tool = cmd[0] if Path(cmd[0]).name.lower().startswith("python") else cmd[0]
        if not Path(tool).resolve().exists():
            QtWidgets.QMessageBox.warning(main_window, "Environnement", "Python introuvable.")
            return
             
        self._run_build(cmd, workdir=cfg.project_dir, log_page=log_page, main_window=main_window)
        
    def _run_build(self, cmd: List[str], workdir: str, log_page, main_window: QtWidgets.QMainWindow):
        # main_window = self.main_window
        self.line_count = 0  # Réinitialiser le compteur de lignes
        self.log_page = log_page  # Stocker la page de log pour les utiliser dans d'autres méthodes
         
        main_window.pages.setCurrentWidget(main_window.page_output)
        main_window.nav.setCurrentRow(4)  # Sélectionner l'onglet "Sortie & Logs"
        log_page.txt_log.clear()
        main_window._build_in_progress = True
        log_page.btn_stop.setEnabled(True)
        log_page.lbl_status.setText("Construction en cours…")
         
        # Afficher la barre de progression
        log_page.progress_bar.setVisible(True)
        log_page.progress_bar.setValue(0)

        self.worker = BuildWorker(cmd, workdir=workdir)
        self.worker.started.connect(lambda c: main_window.log_service.append("$ " + shlex.join(c)))
        self.worker.line.connect(self._update_progress)  # Utiliser la méthode de l'action
        self.worker.line.connect(lambda line: self.log_page.append_log(line, "INFO", update_progress=True))
        self.worker.finished.connect(lambda code: self._on_build_finished(code, main_window))  # Utiliser la méthode de l'action
        self.worker.start()
         
        # Stocker le worker dans main_window pour pouvoir l'arrêter plus tard
        main_window.worker = self.worker
        # Stocker cette instance de BuildAction dans main_window pour que StopBuildAction puisse y accéder
        main_window.current_build_action = self
        
    def _update_progress(self, text: str):
        print(f"_update_progress called with text: {text}")  # Débogage
        self.line_count += 1
        # Indiquer qu'une mise à jour de la progressBar est nécessaire toutes les 10 lignes de log
        if self.line_count % 10 == 0:
            self.pending_progress_update = True
            
    def _update_progress_ui(self):
        # Cette méthode est appelée périodiquement par le timer
        if self.pending_progress_update:
            # main_window = self.main_window
            current_value = self.log_page.progress_bar.value()
            print(f"_update_progress_ui called, current progress bar value: {current_value}")  # Débogage
            if current_value < 100:
                self.log_page.update_progress_bar(current_value + 1)
                print(f"_update_progress_ui called, new progress bar value: {current_value + 1}")  # Débogage
            self.pending_progress_update = False
            
    def _on_build_finished(self, code: int, main_window: QtWidgets.QMainWindow):
        self.line_count = 0  # Réinitialiser le compteur de lignes
        self.pending_progress_update = False  # Réinitialiser le drapeau de mise à jour
        # Arrêter le timer
        if hasattr(self, 'progress_timer'):
            try:
                self.progress_timer.stop()
            except RuntimeError:
                # Le timer C++ a déjà été supprimé, on l'ignore
                pass
        print(f"_on_build_finished called with code: {code}")  # Débogage
        # Cacher la barre de progression
        self.log_page.progress_bar.setVisible(False)
         
        # Copier les répertoires et fichiers spécifiés dans le dossier de sortie
        cfg = main_window._config_from_ui()
        if cfg.output_dir and cfg.directories_to_create:
            try:
                main_window.log_service.append(f"[DEBUG] Chemin de sortie: {cfg.output_dir}", "INFO")
                main_window.log_service.append(f"[DEBUG] Nombre d'éléments à copier: {len(cfg.directories_to_create)}", "INFO")
                for path in cfg.directories_to_create:
                    main_window.log_service.append(f"[DEBUG] Élément à copier: {path}", "INFO")
                    if Path(path).exists():
                        main_window.log_service.append(f"[DEBUG] L'élément existe: {path}", "INFO")
                    else:
                        main_window.log_service.append(f"[DEBUG] L'élément n'existe pas: {path}", "WARNING")
                if cfg.output_dir and cfg.directories_to_create:
                    main_window.file_mgr.copy_items(cfg.directories_to_create, cfg.output_dir, cfg.name)
                    main_window.log_service.append("[INFO] Répertoires et fichiers copiés dans le dossier de sortie.", "INFO")
                 
                # Vérifier si les fichiers ont été copiés
                for path in cfg.directories_to_create:
                    src_path = Path(path)
                    if src_path.exists():
                        dst_path = Path(cfg.output_dir) / src_path.name
                        if dst_path.exists():
                            main_window.log_service.append(f"[DEBUG] Élément copié avec succès: {dst_path}", "INFO")
                        else:
                            main_window.log_service.append(f"[DEBUG] Élément non trouvé après copie: {dst_path}", "WARNING")
            except Exception as e:
                main_window.log_service.append(f"[ERROR] Erreur lors de la copie des répertoires et fichiers: {e}", "ERROR")
         
        # Déplacer le contenu du répertoire créé par PyInstaller à la racine de dist/
        if code == 0 and cfg.output_dir and not cfg.onefile:
            try:
                pyinstall_dir = Path(cfg.output_dir) / cfg.name
                if pyinstall_dir.exists() and pyinstall_dir.is_dir():
                    main_window.log_service.append(f"[DEBUG] Déplacement du contenu de {pyinstall_dir} vers {cfg.output_dir}", "INFO")
                    # Liste des éléments à exclure du déplacement
                    excluded_dirs = ["res"]  # Exclure le dossier res
                    excluded_extensions = [".ico"]  # Exclure les fichiers d'icônes
                    # Le dossier "_internal" et l'exécutable principal sont déplacés par défaut
                    for item in pyinstall_dir.iterdir():
                        # Vérifier si l'élément est dans la liste des dossiers exclus
                        if item.is_dir() and item.name in excluded_dirs:
                            main_window.log_service.append(f"[DEBUG] Dossier exclu du déplacement: {item.name}", "INFO")
                            continue  # Passer à l'élément suivant
                        
                        # Vérifier si l'élément a une extension exclue
                        if item.is_file() and item.suffix.lower() in excluded_extensions:
                            main_window.log_service.append(f"[DEBUG] Fichier exclu du déplacement: {item.name}", "INFO")
                            continue  # Passer à l'élément suivant
                        
                        
                    # Supprimer le répertoire pyinstall_dir s'il est vide
                    # Vérifier s'il est vide avant de le supprimer
                    if not any(pyinstall_dir.iterdir()):
                        pyinstall_dir.rmdir()
                    main_window.log_service.append("[INFO] Contenu déplacé avec succès.", "INFO")
            except Exception as e:
                main_window.log_service.append(f"[ERROR] Erreur lors du déplacement du contenu: {e}", "ERROR")
         
        if code == 0:
            self.log_page.lbl_status.setText("Construction réussie.")
        else:
            self.log_page.lbl_status.setText(f"Construction échouée avec le code {code}.")
        self.log_page.btn_stop.setEnabled(False)
        main_window._build_in_progress = False
        # Nettoyer le worker de main_window
        if hasattr(main_window, 'worker'):
            main_window.worker = None
        # Afficher le message immédiatement, avant les copies de fichiers
              
        # Si l'option "Créer un setup" est cochée, émettre le signal pour créer le setup
        if hasattr(main_window, 'page_project') and main_window.page_project.chk_create_setup.isChecked():
            print("Émettre le signal pour créer le setup")
            # Émettre le signal pour créer le setup
            self.setupCreationRequested.emit()
          
        if code == 0:
            self.log_page.lbl_status.setText("Build terminé avec succès.")
            self.finishRequested.emit()
            QtWidgets.QMessageBox.information(main_window, "Succès", "Build terminé avec succès.")
          
        else:
            QtWidgets.QMessageBox.warning(main_window, "Échec", f"Le build a échoué (code {code}). Consultez les logs.")
        # Ouvrir le dossier de sortie si l'option est activée
        if main_window.open_output_dir and cfg.output_dir and code == 0:
            output_path = Path(cfg.output_dir)
            if output_path.exists():
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(output_path)))
                self.log_page.lbl_status.setText("Dossier de sortie ouvert.")
        # Copier les répertoires et fichiers spécifiés dans le dossier de sortie (après l'affichage du message)
        if code == 0 and cfg.output_dir and cfg.directories_to_create:
            try:
                main_window.log_service.append(f"[DEBUG] Chemin de sortie: {cfg.output_dir}", "INFO")
                main_window.log_service.append(f"[DEBUG] Nombre d'éléments à copier: {len(cfg.directories_to_create)}", "INFO")
                for path in cfg.directories_to_create:
                    main_window.log_service.append(f"[DEBUG] Élément à copier: {path}", "INFO")
                    if Path(path).exists():
                        main_window.log_service.append(f"[DEBUG] L'élément existe: {path}", "INFO")
                    else:
                        main_window.log_service.append(f"[DEBUG] L'élément n'existe pas: {path}", "WARNING")
                if cfg.output_dir and cfg.directories_to_create:
                    main_window.file_mgr.copy_items(cfg.directories_to_create, cfg.output_dir, cfg.name)
                    main_window.log_service.append("[INFO] Répertoires et fichiers copiés dans le dossier de sortie.", "INFO")
                 
                # Vérifier si les fichiers ont été copiés
                for path in cfg.directories_to_create:
                    src_path = Path(path)
                    if src_path.exists():
                        dst_path = Path(cfg.output_dir) / src_path.name
                        if dst_path.exists():
                            main_window.log_service.append(f"[DEBUG] Élément copié avec succès: {dst_path}", "INFO")
                        else:
                            main_window.log_service.append(f"[DEBUG] Élément non trouvé après copie: {dst_path}", "WARNING")
            except Exception as e:
                main_window.log_service.append(f"[ERROR] Erreur lors de la copie des répertoires et fichiers: {e}", "ERROR")


class CleanOutputAction(Action):
    """Action pour nettoyer le dossier de sortie."""
    
    def execute(self):
        main_window = self.main_window
        out = main_window.page_project.ed_output.text().strip()
        if not out:
            QtWidgets.QMessageBox.information(main_window, "Nettoyage", "Aucun dossier de sortie défini.")
            return
            
        main_window.file_mgr.clean_output(out)
        
        p = Path(out)
        if not p.exists():
            QtWidgets.QMessageBox.information(main_window, "Nettoyage", f"{out} n'existe pas.")
            return
            
        confirm_box = QtWidgets.QMessageBox(main_window)
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
                    main_window.log_service.append(f"[CLEAN] Erreur: {e}", "ERROR")
            main_window.log_service.append(f"[CLEAN] {out} vidé.", "INFO")


class AnalyzeProjectAction(Action):
    """Action pour analyser le projet."""
    
    def execute(self):
        main_window = self.main_window
        cfg = main_window._config_from_ui()
        ok, msg = cfg.validate()
        if not ok:
            QtWidgets.QMessageBox.warning(main_window, "Validation", msg)
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
        QtWidgets.QMessageBox.information(main_window, "Analyse", "\n".join(hints) or "Aucun indice particulier.")


class ProfileNewAction(Action):
    """Action pour créer un nouveau profil."""
    
    def execute(self):
        main_window = self.main_window
        name, ok = QtWidgets.QInputDialog.getText(main_window, "Nouveau profil", "Nom du profil :")
        if not ok or not name.strip():
            return
        if main_window.profile_mgr.get(name):
            QtWidgets.QMessageBox.warning(main_window, "Profils", "Ce nom existe déjà.")
            return
        cfg = main_window._config_from_ui()
        main_window.profile_mgr.save(name, cfg)
        main_window._refresh_profiles_list()


class ProfileSaveAction(Action):
    """Action pour sauvegarder le profil courant."""
    
    def execute(self):
        main_window = self.main_window
        item = main_window.page_profiles.widgets['lst_profiles'].currentItem()
        if not item:
            return
        main_window.profile_mgr.save(item.text(), main_window._config_from_ui())
        main_window.log_service.append(f"Profil sauvegardé: {item.text()}", "INFO")


class ProfileDeleteAction(Action):
    """Action pour supprimer le profil sélectionné."""
    
    def execute(self):
        main_window = self.main_window
        item = main_window.page_profiles.widgets['lst_profiles'].currentItem()
        if not item:
            return
        main_window.profile_mgr.delete(item.text())
        main_window._refresh_profiles_list()
        main_window.log_service.append(f"Profil supprimé: {item.text()}", "INFO")


class ProfileExportAction(Action):
    """Action pour exporter les profils."""
    
    def execute(self):
        main_window = self.main_window
        path, _ = QtWidgets.QFileDialog.getSaveFileName(main_window, "Exporter profils", filter="JSON (*.json)")
        if not path:
            return
        main_window.profile_mgr.export_to_file(path)
        main_window.log_service.append(f"Profils exportés -> {path}", "INFO")


class ProfileImportAction(Action):
    """Action pour importer des profils."""
    
    def execute(self):
        main_window = self.main_window
        path, _ = QtWidgets.QFileDialog.getOpenFileName(main_window, "Importer profils", filter="JSON (*.json)")
        if not path:
            return
        try:
            main_window.profile_mgr.import_from_file(path)
            main_window._refresh_profiles_list()
            main_window.log_service.append(f"Profils importés depuis {path}", "INFO")
        except Exception as e:
            main_window.log_service.append(f"Erreur import profils: {e}", "ERROR")
            QtWidgets.QMessageBox.warning(main_window, "Import", f"Erreur: {e}")


class InstallAppAction(Action):
    """Action pour installer l'application."""
    
    def execute(self):
        main_window = self.main_window
        # Récupérer les valeurs des widgets de la page d'installation
        widgets = main_window.page_install.widgets
        
        app_name = widgets['app_name'].text() or "MyApp"
        dest_path = widgets['dest_path'].text()
        wizard_image = widgets['wizard_image'].text()
        
        # Vérifier que le chemin de destination n'est pas vide
        if not dest_path:
            QtWidgets.QMessageBox.warning(main_window, "Erreur", "Veuillez sélectionner un dossier de destination.")
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


class CreateSetupExeAction(BaseBuildAction):
    """Action pour créer l'exécutable setup.exe à partir de install_wizard.py."""
    
    finishRequested = QtCore.Signal()
    
    def __init__(self, log_page):
        super().__init__(log_page)  # Initialiser BaseBuildAction
        
    def execute(self):
        import subprocess
        import sys
        import os
        from pathlib import Path
        
        log_page = self.log_page  # log_page est stocké dans self.log_page
        # Essayer de récupérer main_window via le parent de log_page
        # log_page est self.page_output (OutputTabPage) dont le parent est self.pages (QStackedWidget)
        # Le parent de self.pages est central (QWidget), et le parent de central est MainWindow
        pages_widget = log_page.parentWidget()
        if pages_widget is None:
            print("Erreur: Impossible de récupérer pages_widget depuis log_page")
            QtWidgets.QMessageBox.critical(log_page, "Erreur", "Impossible de récupérer le widget pages.")
            return
            
        central_widget = pages_widget.parentWidget()
        if central_widget is None:
            print("Erreur: Impossible de récupérer central_widget depuis pages_widget")
            QtWidgets.QMessageBox.critical(log_page, "Erreur", "Impossible de récupérer le widget central.")
            return
            
        main_window = central_widget.parentWidget()
        if main_window is None:
            print("Erreur: Impossible de récupérer main_window depuis central_widget")
            QtWidgets.QMessageBox.critical(log_page, "Erreur", "Impossible de récupérer la fenêtre principale.")
            return
            
        # Définir les chemins
        project_root = Path(__file__).parent.parent # e:\Projets QT\Installer builder
        spec_file = project_root / "src" / "install_wizard.spec"
        dist_path = project_root / "dist_setup"
        
        if not spec_file.exists():
            QtWidgets.QMessageBox.critical(main_window, "Erreur", f"Fichier spec introuvable: {spec_file}")
            return
            
        # Préparer la commande PyInstaller
        # Utiliser le même interpréteur Python que celui qui exécute l'application
        cmd = [
            sys.executable, "-m", "PyInstaller",
            str(spec_file),
            f"--distpath={dist_path}",
            "--noconfirm", # Ne pas demander de confirmation
            "--clean" # Nettoyer avant de construire
        ]
        
        # Configurer l'interface utilisateur pour le build
        self._setup_ui_for_build(main_window, "Création de setup.exe en cours…")
        
        try:
            log_page.append_log(f"Exécution de la commande: {' '.join(cmd)}", "INFO")
            # Exécuter la commande et capturer la sortie
            # Utiliser stdout et stderr combinés pour avoir tout le log
            process = subprocess.Popen(
                cmd,
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Rediriger stderr vers stdout
                text=True,
                encoding='utf-8',
                errors='replace' # Gérer les erreurs d'encodage
            )
            
            # Lire la sortie ligne par ligne
            for line in process.stdout:
                line = line.rstrip('\n\r') # Nettoyer les fins de ligne
                if line: # N'afficher que les lignes non vides
                    log_page.append_log(line, "INFO")
                QtWidgets.QApplication.processEvents() # Garder l'UI réactive
            
            # Attendre la fin du processus
            return_code = process.wait()
            
            # Cacher la barre de progression
            log_page.progress_bar.setVisible(False)
            
            if return_code == 0:
                log_page.lbl_status.setText("Création de setup.exe réussie.")
                
                # Déplacer setup.exe vers le répertoire de destination
                setup_exe_path = dist_path / "setup.exe"
                if setup_exe_path.exists():
                    # Récupérer la configuration de l'interface utilisateur
                    cfg = main_window._config_from_ui()
                    # Déterminer le chemin de destination
                    destination_dir = Path(cfg.output_dir) / cfg.name
                    destination_dir.mkdir(parents=True, exist_ok=True)
                    destination_path = destination_dir / "setup.exe"
                    
                    try:
                        # Déplacer le fichier
                        setup_exe_path.rename(destination_path)
                        QtWidgets.QMessageBox.information(main_window, "Succès", f"setup.exe créé et déplacé avec succès dans:\n{destination_path}")
                        # Ouvrir le dossier de destination
                        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(destination_dir)))
                    except Exception as e:
                        QtWidgets.QMessageBox.warning(main_window, "Erreur", f"Erreur lors du déplacement de setup.exe: {e}")
                else:
                    QtWidgets.QMessageBox.information(main_window, "Succès", f"setup.exe créé avec succès dans:\n{dist_path}")
                    # Ouvrir le dossier de sortie
                    QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(dist_path)))
            else:
                log_page.lbl_status.setText(f"Création de setup.exe échouée (code {return_code}).")
                QtWidgets.QMessageBox.warning(main_window, "Échec", f"La création de setup.exe a échoué (code {return_code}). Consultez les logs.")
                
        except FileNotFoundError:
            # Cacher la barre de progression
            log_page.progress_bar.setVisible(False)
            log_page.lbl_status.setText("PyInstaller introuvable.")
            QtWidgets.QMessageBox.critical(main_window, "Erreur", "PyInstaller introuvable. Veuillez l'installer avec 'pip install pyinstaller'.")
        except Exception as e:
            # Cacher la barre de progression
            log_page.progress_bar.setVisible(False)
            log_page.lbl_status.setText("Erreur lors de la création de setup.exe.")
            QtWidgets.QMessageBox.critical(main_window, "Erreur", f"Une erreur s'est produite:\n{str(e)}")
        finally:
            self.finishRequested.emit()
            # Réactiver le bouton stop si nécessaire (normalement il ne devrait pas être pertinent ici)
            # log_page.btn_stop.setEnabled(True)
            pass
            
            
from pathlib import Path
import shutil
from enum import Enum


class FileOperation(Enum):
    """Enum pour les opérations disponibles sur les fichiers."""
    MOVE = "move"
    COPY = "copy"
    DELETE = "delete"
    RENAME = "rename"


from pathlib import Path
import shutil
from enum import Enum


class FileOperation(Enum):
    """Enum pour les opérations disponibles sur les fichiers."""
    MOVE = "move"
    COPY = "copy"
    DELETE = "delete"
    RENAME = "rename"


class FileAction:
    """Classe générique pour gérer les actions sur les fichiers."""

    def __init__(self, main_window,
                 app_root: str,
                 operation: FileOperation = FileOperation.MOVE,
                 create_dir: bool = True,
                 auto_rename: bool = True,
                 confirm_overwrite: bool = False):
        """
        :param main_window: Fenêtre principale pour logs et QMessageBox
        :param app_root: Dossier racine de l'application (sera créé si inexistant)
        :param operation: Type d'opération à exécuter (FileOperation)
        :param create_dir: Crée le dossier de destination si nécessaire
        :param auto_rename: Renomme automatiquement si conflit de fichier
        :param confirm_overwrite: Demande confirmation avant d'écraser un fichier
        """
        self.main_window = main_window
        self.app_root = Path(app_root)
        self.operation = operation
        self.create_dir = create_dir
        self.auto_rename = auto_rename
        self.confirm_overwrite = confirm_overwrite

        self._ensure_app_root()

    # ----------- Vérification / création du dossier racine -----------
    def _ensure_app_root(self):
        """Vérifie ou crée le dossier racine de l'application."""
        try:
            if not self.app_root.exists():
                self.app_root.mkdir(parents=True, exist_ok=True)
                self.main_window.log_service.append(
                    f"[FILE] Dossier racine créé: {self.app_root}", "INFO"
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self.main_window,
                "Erreur",
                f"Impossible de créer le dossier racine de l'application:\n{self.app_root}\n{str(e)}"
            )
            raise

    # ----------- Méthodes utilitaires -----------
    def _get_unique_filename(self, dest_file: Path) -> Path:
        counter = 1
        new_dest = dest_file
        while new_dest.exists():
            new_dest = dest_file.with_stem(f"{dest_file.stem}_{counter}")
            counter += 1
        return new_dest

    def _ensure_destination_dir(self, dest_file: Path) -> bool:
        """Crée le dossier de destination si nécessaire (dans app_root si relatif)."""
        dest_dir = dest_file.parent

        # Si le chemin est relatif -> basé sur app_root
        if not dest_file.is_absolute():
            dest_dir = self.app_root / dest_dir
            dest_file = self.app_root / dest_file

        if not dest_dir.exists():
            if self.create_dir:
                try:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    self.main_window.log_service.append(f"[FILE] Dossier créé: {dest_dir}", "INFO")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(
                        self.main_window,
                        "Erreur",
                        f"Impossible de créer le dossier: {dest_dir}\n{str(e)}"
                    )
                    return False
            else:
                QtWidgets.QMessageBox.warning(
                    self.main_window,
                    "Erreur",
                    f"Le dossier de destination n'existe pas: {dest_dir}"
                )
                return False
        return True

    def _handle_conflict(self, dest_file: Path) -> Path | None:
        if not dest_file.exists():
            return dest_file

        if self.confirm_overwrite:
            reply = QtWidgets.QMessageBox.question(
                self.main_window,
                "Conflit de fichier",
                f"Le fichier {dest_file} existe déjà.\nVoulez-vous l'écraser ?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.No:
                return self._get_unique_filename(dest_file) if self.auto_rename else None
        elif self.auto_rename:
            return self._get_unique_filename(dest_file)
        return dest_file

    # ----------- Méthodes d'opérations -----------
    def _move_file(self, source_file: Path, dest_file: Path):
        if not self._ensure_destination_dir(dest_file):
            return
        dest_file = self._handle_conflict(dest_file)
        if dest_file is None:
            return
        shutil.move(str(source_file), str(dest_file))
        self.main_window.log_service.append(f"[FILE] Déplacé: {source_file} -> {dest_file}", "INFO")
        #QtWidgets.QMessageBox.information(
        #    self.main_window,
        #    "Succès",
        #    f"Fichier déplacé:\n{source_file}\n->\n{dest_file}"
        #)

    def _copy_file(self, source_file: Path, dest_file: Path):
        if not self._ensure_destination_dir(dest_file):
            return
        dest_file = self._handle_conflict(dest_file)
        if dest_file is None:
            return
        shutil.copy2(str(source_file), str(dest_file))
        self.main_window.log_service.append(f"[FILE] Copié: {source_file} -> {dest_file}", "INFO")
        #QtWidgets.QMessageBox.information(
        #    self.main_window,
        #    "Succès",
        #    f"Fichier copié:\n{source_file}\n->\n{dest_file}"
        #)

    def _delete_file(self, source_file: Path):
        source_file.unlink(missing_ok=True)
        self.main_window.log_service.append(f"[FILE] Supprimé: {source_file}", "INFO")
        #QtWidgets.QMessageBox.information(self.main_window, "Succès", f"Fichier supprimé:\n{source_file}")

    def _rename_file(self, source_file: Path, dest_file: Path):
        if not self._ensure_destination_dir(dest_file):
            return
        dest_file = self._handle_conflict(dest_file)
        if dest_file is None:
            return
        source_file.rename(dest_file)
        self.main_window.log_service.append(f"[FILE] Renommé: {source_file} -> {dest_file}", "INFO")
        #QtWidgets.QMessageBox.information(
        #    self.main_window,
        #    "Succès",
        #    f"Fichier renommé:\n{source_file}\n->\n{dest_file}"
        #)

    # ----------- Routeur principal -----------
    def execute(self, source_path: str, dest_path: str = None):
        source_file = Path(source_path)

        if not source_file.exists() and self.operation != FileOperation.DELETE:
            error_msg = f"Le fichier source n'existe pas: {source_file}"
            QtWidgets.QMessageBox.warning(self.main_window, "Erreur", error_msg)
            self.main_window.log_service.append(f"[FILE] {error_msg}", "ERROR")
            return

        try:
            if self.operation == FileOperation.MOVE:
                if not dest_path:
                    raise ValueError("dest_path est requis pour MOVE")
                self._move_file(source_file, Path(dest_path))

            elif self.operation == FileOperation.COPY:
                if not dest_path:
                    raise ValueError("dest_path est requis pour COPY")
                self._copy_file(source_file, Path(dest_path))

            elif self.operation == FileOperation.DELETE:
                self._delete_file(source_file)

            elif self.operation == FileOperation.RENAME:
                if not dest_path:
                    raise ValueError("dest_path est requis pour RENAME")
                self._rename_file(source_file, Path(dest_path))

            else:
                raise ValueError(f"Opération inconnue: {self.operation}")

        except Exception as e:
            error_msg = f"Erreur lors de l'opération {self.operation.value}:\n{str(e)}"
            QtWidgets.QMessageBox.critical(self.main_window, "Erreur", error_msg)
            self.main_window.log_service.append(f"[FILE] {error_msg}", "ERROR")

    """Classe générique pour gérer les actions sur les fichiers."""

    def __init__(self, main_window,
                 operation: FileOperation = FileOperation.MOVE,
                 create_dir: bool = True,
                 auto_rename: bool = True,
                 confirm_overwrite: bool = False):
        """
        :param main_window: Fenêtre principale pour logs et QMessageBox
        :param operation: Type d'opération à exécuter (FileOperation)
        :param create_dir: Crée le dossier de destination si nécessaire (pour move/copy)
        :param auto_rename: Renomme automatiquement si conflit de fichier
        :param confirm_overwrite: Demande confirmation avant d'écraser un fichier
        """
        self.main_window = main_window
        self.operation = operation
        self.create_dir = create_dir
        self.auto_rename = auto_rename
        self.confirm_overwrite = confirm_overwrite

    # ----------- Méthodes utilitaires -----------
    def _get_unique_filename(self, dest_file: Path) -> Path:
        """Renvoie un nom unique si le fichier existe déjà (ex: fichier_1.txt)."""
        counter = 1
        new_dest = dest_file
        while new_dest.exists():
            new_dest = dest_file.with_stem(f"{dest_file.stem}_{counter}")
            counter += 1
        return new_dest

    def _ensure_destination_dir(self, dest_file: Path) -> bool:
        """Crée le dossier de destination si nécessaire, renvoie False si impossible."""
        if not dest_file.parent.exists():
            if self.create_dir:
                try:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    self.main_window.log_service.append(f"[FILE] Dossier créé: {dest_file.parent}", "INFO")
                    return True
                except Exception as e:
                    error_msg = f"Impossible de créer le dossier: {dest_file.parent}\n{str(e)}"
                    QtWidgets.QMessageBox.critical(self.main_window, "Erreur", error_msg)
                    self.main_window.log_service.append(f"[FILE] {error_msg}", "ERROR")
                    return False
            else:
                error_msg = f"Le dossier de destination n'existe pas: {dest_file.parent}"
                QtWidgets.QMessageBox.warning(self.main_window, "Erreur", error_msg)
                self.main_window.log_service.append(f"[FILE] {error_msg}", "ERROR")
                return False
        return True

    def _handle_conflict(self, dest_file: Path) -> Path | None:
        """Gère les conflits de fichier (confirme ou renomme). Renvoie le fichier final ou None pour annuler."""
        if not dest_file.exists():
            return dest_file

        if self.confirm_overwrite:
            reply = QtWidgets.QMessageBox.question(
                self.main_window,
                "Conflit de fichier",
                f"Le fichier {dest_file} existe déjà.\nVoulez-vous l'écraser ?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.No:
                if self.auto_rename:
                    return self._get_unique_filename(dest_file)
                return None
        elif self.auto_rename:
            return self._get_unique_filename(dest_file)

        return dest_file

    # ----------- Méthodes d'opérations -----------
    def _move_file(self, source_file: Path, dest_file: Path):
        if not self._ensure_destination_dir(dest_file):
            return

        dest_file = self._handle_conflict(dest_file)
        if dest_file is None:
            return  # Annulé par l'utilisateur

        shutil.move(str(source_file), str(dest_file))
        self.main_window.log_service.append(f"[FILE] Déplacé: {source_file} -> {dest_file}", "INFO")
        QtWidgets.QMessageBox.information(
            self.main_window,
            "Succès",
            f"Fichier déplacé avec succès:\n{source_file}\n->\n{dest_file}"
        )

    def _copy_file(self, source_file: Path, dest_file: Path):
        if not self._ensure_destination_dir(dest_file):
            return

        dest_file = self._handle_conflict(dest_file)
        if dest_file is None:
            return  # Annulé par l'utilisateur

        shutil.copy2(str(source_file), str(dest_file))
        self.main_window.log_service.append(f"[FILE] Copié: {source_file} -> {dest_file}", "INFO")
        QtWidgets.QMessageBox.information(
            self.main_window,
            "Succès",
            f"Fichier copié avec succès:\n{source_file}\n->\n{dest_file}"
        )

    def _delete_file(self, source_file: Path):
        source_file.unlink(missing_ok=True)
        self.main_window.log_service.append(f"[FILE] Supprimé: {source_file}", "INFO")
        QtWidgets.QMessageBox.information(self.main_window, "Succès", f"Fichier supprimé:\n{source_file}")

    def _rename_file(self, source_file: Path, dest_file: Path):
        if not self._ensure_destination_dir(dest_file):
            return

        dest_file = self._handle_conflict(dest_file)
        if dest_file is None:
            return  # Annulé par l'utilisateur

        source_file.rename(dest_file)
        self.main_window.log_service.append(f"[FILE] Renommé: {source_file} -> {dest_file}", "INFO")
        QtWidgets.QMessageBox.information(
            self.main_window,
            "Succès",
            f"Fichier renommé:\n{source_file}\n->\n{dest_file}"
        )

    # ----------- Méthode principale -----------
    def execute(self, source_path: str, dest_path: str = None):
        source_file = Path(source_path)

        if not source_file.exists() and self.operation != FileOperation.DELETE:
            error_msg = f"Le fichier source n'existe pas: {source_file}"
            QtWidgets.QMessageBox.warning(self.main_window, "Erreur", error_msg)
            self.main_window.log_service.append(f"[FILE] {error_msg}", "ERROR")
            return

        try:
            if self.operation == FileOperation.MOVE:
                if not dest_path:
                    raise ValueError("dest_path est requis pour MOVE")
                self._move_file(source_file, Path(dest_path))

            elif self.operation == FileOperation.COPY:
                if not dest_path:
                    raise ValueError("dest_path est requis pour COPY")
                self._copy_file(source_file, Path(dest_path))

            elif self.operation == FileOperation.DELETE:
                self._delete_file(source_file)

            elif self.operation == FileOperation.RENAME:
                if not dest_path:
                    raise ValueError("dest_path est requis pour RENAME")
                self._rename_file(source_file, Path(dest_path))

            else:
                raise ValueError(f"Opération inconnue: {self.operation}")

        except Exception as e:
            error_msg = f"Erreur lors de l'opération {self.operation.value}:\n{str(e)}"
            QtWidgets.QMessageBox.critical(self.main_window, "Erreur", error_msg)
            self.main_window.log_service.append(f"[FILE] {error_msg}", "ERROR")


