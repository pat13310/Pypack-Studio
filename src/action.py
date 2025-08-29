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


class Action(ABC):
    """Classe de base abstraite pour toutes les actions de l'application."""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    @abstractmethod
    def execute(self):
        """Exécute l'action."""
        pass


class BuildAction(Action):
    """Action pour construire l'application."""
    
    def __init__(self, log_page):
        super().__init__(log_page)  # log_page est stocké dans self.main_window
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
        if code == 0:
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


class CreateSetupExeAction(Action):
    """Action pour créer l'exécutable setup.exe à partir de install_wizard.py."""
    
    def __init__(self, log_page):
        super().__init__(log_page)  # log_page est stocké dans self.main_window
        
    def execute(self):
        import subprocess
        import sys
        import os
        from pathlib import Path
        
        log_page = self.main_window  # log_page est stocké dans self.main_window
        # Essayer de récupérer main_window via le parent de log_page
        main_window = log_page.parentWidget()
        if main_window is None:
            print("Erreur: Impossible de récupérer main_window depuis log_page")
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
        main_window.pages.setCurrentWidget(main_window.page_output)
        main_window.nav.setCurrentRow(4)  # Sélectionner l'onglet "Sortie & Logs"
        log_page.txt_log.clear()
        log_page.lbl_status.setText("Création de setup.exe en cours…")
        log_page.btn_stop.setEnabled(False) # Désactiver le bouton stop pour cette action simple
        log_page.progress_bar.setVisible(True)
        log_page.progress_bar.setRange(0, 0) # Barre de progression indéterminée
        log_page.progress_bar.setValue(0)
        
        QtWidgets.QApplication.processEvents() # Forcer la mise à jour de l'UI
        
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
            # Réactiver le bouton stop si nécessaire (normalement il ne devrait pas être pertinent ici)
            # log_page.btn_stop.setEnabled(True) 
            pass