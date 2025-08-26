"""
Assistant d'installation de PyPack Studio
"""

import sys
import os
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets


class WizardConfig:
    def __init__(self, app_name: str = "MyApp", dest_path: str = None, wizard_image: str = None, app_description: str = ""):
        # Informations de base
        self.app_name = app_name
        self.dest_path = dest_path
        self.wizard_image = wizard_image
        self.app_description = app_description
        
        # Textes du wizard
        self.intro_title = "Bienvenue dans l'assistant de création d'application PySide6"
        self.intro_subtitle = "Cet assistant va vous aider à créer une structure de base pour votre application."
        self.intro_text = "Cette application va créer une structure de base pour une application PySide6 avec les éléments nécessaires pour commencer à développer.\n\nCliquez sur Suivant pour continuer."
        
        self.app_info_title = "Informations sur l'application"
        self.app_info_subtitle = "Veuillez entrer les informations de base pour votre application."
        
        self.components_title = "Composants"
        self.components_subtitle = "Sélectionnez les composants à inclure dans votre application."
        
        self.install_options_title = "Options d'installation"
        self.install_options_subtitle = "Sélectionnez les options d'installation pour votre application."
        
        self.destination_title = "Destination"
        self.destination_subtitle = "Choisissez le répertoire où créer votre application."
        
        self.summary_title = "Résumé"
        self.summary_subtitle = "Voici un résumé de vos choix. Cliquez sur Terminer pour quitter l'assistant."

class InstallWizard(QtWidgets.QWizard):
    def __init__(self, config: WizardConfig = None):
        super().__init__()
        self.config = config or WizardConfig()
        
        # Définir les propriétés à partir de la configuration
        self.app_name = self.config.app_name
        self.dest_path = self.config.dest_path or str(Path.home() / self.app_name)
        self.wizard_image = self.config.wizard_image

        self.setWindowTitle("Assistant d'installation de PyPack Studio")
        self.resize(800, 360)

        # Définir le style de l'assistant
        self.setWizardStyle(QtWidgets.QWizard.ModernStyle)

        # Traduire les boutons en français
        self.setButtonText(QtWidgets.QWizard.BackButton, "Précédent")
        self.setButtonText(QtWidgets.QWizard.NextButton, "Suivant")
        self.setButtonText(QtWidgets.QWizard.CancelButton, "Annuler")
        self.setButtonText(QtWidgets.QWizard.FinishButton, "Installer")

        # Ajout des pages
        self.addPage(self.create_intro_page())
        self.addPage(self.create_app_info_page())
        self.addPage(self.create_destination_page())
        self.addPage(self.create_components_page())
        self.addPage(self.create_install_options_page())
        self.addPage(self.create_summary_page())

        # Définir l'icône de la fenêtre
        if os.path.exists("pypack.ico"):
            self.setWindowIcon(QtGui.QIcon("pypack.ico"))
        elif os.path.exists("pypack.png"):
            self.setWindowIcon(QtGui.QIcon("pypack.png"))

        # Définir l'image de fond pour le côté gauche
        self.set_wizard_image()

        # Connecter le bouton "Installer" à la méthode d'installation
        self.button(QtWidgets.QWizard.FinishButton).clicked.connect(self.create_project)

    def set_wizard_image(self):
        target_width = 280
        target_height = 270
        left_margin = 8
        separator_width = 2

        image_path = None
        # Utiliser l'image personnalisée si elle est fournie et existe
        if self.config.wizard_image and os.path.exists(self.config.wizard_image):
            image_path = self.config.wizard_image
        elif os.path.exists("wizard.png"):
            image_path = "wizard.png"
        elif os.path.exists("projet.png"):
            image_path = "projet.png"
        elif os.path.exists("pypack.png"):
            image_path = "pypack.png"

        if image_path:
            pixmap = QtGui.QPixmap(image_path)
            if not pixmap.isNull():
                # Préserver le format de l'image source s'il a un canal alpha
                if pixmap.hasAlpha():
                    pixmap = pixmap.convertToFormat(QtGui.QImage.Format_ARGB32)
                
                if pixmap.width() > target_width or pixmap.height() > target_height:
                    scaled_width = target_width - left_margin - separator_width
                    # Utiliser Qt.SmoothTransformation et préserver l'alpha
                    pixmap = pixmap.scaled(
                        scaled_width,
                        target_height,
                        QtCore.Qt.KeepAspectRatio,
                        QtCore.Qt.SmoothTransformation,
                    )
                
                # Créer un nouveau pixmap avec support de la transparence
                new_pixmap = QtGui.QPixmap(target_width, target_height)
                new_pixmap.fill(QtCore.Qt.transparent)
                
                # Utiliser un QPainter pour composer l'image avec transparence
                painter = QtGui.QPainter(new_pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
                
                # Dessiner la ligne de séparation
                painter.setPen(QtGui.QPen(QtCore.Qt.lightGray, separator_width))
                painter.drawLine(
                    target_width - separator_width // 2,
                    0,
                    target_width - separator_width // 2,
                    target_height,
                )
                
                # Dessiner l'image avec composition qui préserve l'alpha
                painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
                painter.drawPixmap(left_margin, 0, pixmap)
                painter.end()
                
                self.setPixmap(QtWidgets.QWizard.WatermarkPixmap, new_pixmap)
            else:
                print(f"Erreur: Impossible de charger l'image {image_path}")
        else:
            print("Aucune image trouvée pour l'assistant")

    def create_intro_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle(self.config.intro_title)
        page.setSubTitle(self.config.intro_subtitle)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setLineWidth(1)
        separator.setStyleSheet("QFrame { color: #5a9bff; background: #5a9bff; }")
        separator.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        label = QtWidgets.QLabel(self.config.intro_text)
        label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(page)
        layout.setSpacing(0)
        layout.addWidget(separator)
        layout.addWidget(label)

        return page

    def create_app_info_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle(self.config.app_info_title)
        page.setSubTitle(self.config.app_info_subtitle)

        name_label = QtWidgets.QLabel("Nom de l'application:")
        self.name_edit = QtWidgets.QLineEdit(self.app_name)
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)

        desc_label = QtWidgets.QLabel("Description:")
        self.desc_edit = QtWidgets.QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        desc_layout = QtWidgets.QVBoxLayout()
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)

        layout = QtWidgets.QVBoxLayout(page)
        layout.addLayout(name_layout)
        layout.addLayout(desc_layout)

        page.registerField("app_name*", self.name_edit)
        return page

    def create_components_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle(self.config.components_title)
        page.setSubTitle(self.config.components_subtitle)

        self.pyside_check = QtWidgets.QCheckBox("PySide6")
        self.pyside_check.setChecked(True)
        self.pyside_check.setEnabled(False)

        self.structure_check = QtWidgets.QCheckBox(
            "Structure de base (main.py, resources, etc.)"
        )
        self.structure_check.setChecked(True)
        self.structure_check.setEnabled(False)

        self.requirements_check = QtWidgets.QCheckBox("Fichier requirements.txt")
        self.requirements_check.setChecked(True)

        self.pyinstaller_check = QtWidgets.QCheckBox(
            "Fichier de configuration PyInstaller (.spec)"
        )
        self.pyinstaller_check.setChecked(True)

        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(self.pyside_check)
        layout.addWidget(self.structure_check)
        layout.addWidget(self.requirements_check)
        layout.addWidget(self.pyinstaller_check)

        return page

    def create_install_options_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle(self.config.install_options_title)
        page.setSubTitle(self.config.install_options_subtitle)

        self.desktop_shortcut_check = QtWidgets.QCheckBox("Créer un raccourci sur le bureau")
        self.desktop_shortcut_check.setChecked(True)

        self.start_menu_check = QtWidgets.QCheckBox("Ajouter au menu Démarrer")
        self.start_menu_check.setChecked(True)

        self.file_association_check = QtWidgets.QCheckBox("Associer les fichiers .mypack à cette application")
        self.file_association_check.setChecked(False)

        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(self.desktop_shortcut_check)
        layout.addWidget(self.start_menu_check)
        layout.addWidget(self.file_association_check)

        return page

    def create_destination_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle(self.config.destination_title)
        page.setSubTitle(self.config.destination_subtitle)

        dest_label = QtWidgets.QLabel("Répertoire de destination:")
        self.dest_edit = QtWidgets.QLineEdit()
        self.dest_edit.setText(self.dest_path)
        browse_btn = QtWidgets.QPushButton("Parcourir...")
        browse_btn.clicked.connect(self.browse_destination)

        dest_layout = QtWidgets.QHBoxLayout()
        dest_layout.addWidget(dest_label)
        dest_layout.addWidget(self.dest_edit)
        dest_layout.addWidget(browse_btn)

        layout = QtWidgets.QVBoxLayout(page)
        layout.addLayout(dest_layout)

        page.registerField("dest_path*", self.dest_edit)
        return page

    def create_summary_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle(self.config.summary_title)
        page.setSubTitle(self.config.summary_subtitle)
        page.setFinalPage(True)  # ✅ dernière page

        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(self.summary_label)

        return page

    def browse_destination(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choisir le répertoire de destination"
        )
        if directory:
            self.dest_edit.setText(directory)

    def initializePage(self, id):
        if self.page(id).title() == "Résumé":
            app_name = self.field("app_name")
            dest_path = self.field("dest_path")

            summary = f"""
            <b>Nom de l'application:</b> {app_name}<br/>
            <b>Répertoire de destination:</b> {dest_path}<br/>
            <b>Composants inclus:</b><br/>
            """
            components = []
            if self.pyside_check.isChecked():
                components.append("• PySide6")
            if self.structure_check.isChecked():
                components.append("• Structure de base")
            if self.requirements_check.isChecked():
                components.append("• requirements.txt")
            if self.pyinstaller_check.isChecked():
                components.append("• Fichier de configuration PyInstaller")

            summary += "<br/>".join(components)
            self.summary_label.setText(summary)

    def create_project(self):
        app_name = self.field("app_name")
        dest_path = Path(self.field("dest_path"))

        try:
            print(f"Création du projet {app_name} dans {dest_path}")
            dest_path.mkdir(parents=True, exist_ok=True)

            src_path = Path("dist") / app_name
            if not src_path.exists():
                src_path.mkdir(parents=True, exist_ok=True)
                self.create_basic_structure(src_path, app_name)
                if self.requirements_check.isChecked():
                    self.create_requirements_file(src_path)
                if self.pyinstaller_check.isChecked():
                    self.create_pyinstaller_spec(src_path, app_name)

            self.copy_app_files(app_name, dest_path)
            self.create_setup_exe(dest_path, app_name)

            QtWidgets.QMessageBox.information(
                self,
                "Succès",
                f"Le projet '{app_name}' a été installé avec succès dans:\n{dest_path}",
            )

            # ✅ Aller à la page suivante (Résumé)
            self.next()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur s'est produite lors de l'installation du projet:\n{str(e)}",
            )

    def copy_app_files(self, app_name, dest_path):
        import shutil

        src_path = Path("dist") / app_name
        if not src_path.exists():
            raise FileNotFoundError(
                f"Le répertoire {src_path} n'existe pas. Veuillez d'abord construire l'application."
            )

        for item in src_path.iterdir():
            if item.is_dir():
                shutil.copytree(item, dest_path / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest_path)

    def create_setup_exe(self, dest_path, app_name):
        setup_bat_content = f"""@echo off
echo Installation de {app_name}...
echo Copie des fichiers...
xcopy /E /I /Y ".\\*" "%PROGRAMFILES%\\{app_name}"
echo Création du raccourci...
set "shortcut_path=%USERPROFILE%\\Desktop\\{app_name}.lnk"
powershell -Command "$s = New-Object -ComObject WScript.Shell; $shortcut = $s.CreateShortcut('%shortcut_path%'); $shortcut.TargetPath = '%PROGRAMFILES%\\{app_name}\\{app_name}.exe'; $shortcut.Save()"
echo Installation terminée.
pause
"""
        with open(dest_path / "setup.bat", "w", encoding="utf-8") as f:
            f.write(setup_bat_content)

        setup_exe_content = f"""@echo off
call ".\\setup.bat"
"""
        with open(dest_path / "setup.exe", "w", encoding="utf-8") as f:
            f.write(setup_exe_content)

    def create_basic_structure(self, dest_path, app_name):
        main_py_content = f'''"""
Application {app_name}
"""

import sys
from PySide6 import QtCore, QtGui, QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("{app_name}")
        self.resize(800, 600)
        
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        label = QtWidgets.QLabel("Bienvenue dans {app_name}!")
        label.setAlignment(QtCore.Qt.AlignCenter)
        font = label.font()
        font.setPointSize(18)
        label.setFont(font)
        layout.addWidget(label)
        
        button = QtWidgets.QPushButton("Cliquez-moi")
        button.clicked.connect(self.on_button_clicked)
        layout.addWidget(button)
        
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setPlaceholderText("Entrez votre texte ici...")
        layout.addWidget(self.text_edit)
    
    def on_button_clicked(self):
        self.text_edit.append("Bonjour, monde!")


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
'''
        with open(dest_path / "main.py", "w", encoding="utf-8") as f:
            f.write(main_py_content)

        resources_path = dest_path / "resources"
        resources_path.mkdir(exist_ok=True)

        readme_content = f"""# {app_name}

## Description
{self.config.app_description}

## Structure du projet
- `main.py`: Point d'entrée de l'application
- `resources/`: Répertoire pour les ressources
- `requirements.txt`: Dépendances du projet
- `pypack.spec`: Fichier de configuration PyInstaller

## Installation
1. Créez un environnement virtuel:
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\\Scripts\\activate

2. Installez les dépendances:
   pip install -r requirements.txt

3. Exécutez l'application:
   python main.py

## Création d'un exécutable
pyinstaller pypack.spec
"""
        with open(dest_path / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

    def create_requirements_file(self, dest_path):
        requirements_content = """PySide6>=6.0.0
"""
        with open(dest_path / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content)

    def create_pyinstaller_spec(self, dest_path, app_name):
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico'
)
"""
        with open(dest_path / f"{app_name.lower()}.spec", "w", encoding="utf-8") as f:
            f.write(spec_content)


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    app.setStyleSheet(
        """
    QWizard {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                    stop: 0 #2e2e2e, stop: 1 #1a1a1a);
        color: #ffffff;
    }
    QWizardPage {
        background: transparent;
        color: #ffffff;
    }
    QLabel {
        color: #e0e0e0;
    }
    QLineEdit, QTextEdit, QCheckBox {
        background-color: #2d2d2d;
        border: 1px solid #4a4a4a;
        border-radius: 4px;
        padding: 4px;
        color: #ffffff;
    }
    QPushButton {
        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5a5a5a, stop: 1 #3c3c3c);
        border: 1px solid #4a4a4a;
        border-radius: 6px;
        padding: 6px 12px;
        color: #ffffff;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #6a6a6a, stop: 1 #4c4c4c);
        border: 1px solid #5a9bff;
    }
    QPushButton:pressed {
        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #3c3c3c, stop: 1 #5a5a5a);
        border: 1px solid #2a2a2a;
    }
    """
    )
    
    wizard = InstallWizard()
    
    # Centrer horizontalement et positionner à 5 pixels du haut
    screen_size = app.primaryScreen().size()
    window_width = wizard.width()
    x = (screen_size.width() - window_width) // 2
    wizard.move(x, 5)
    
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
