"""
Assistant d'installation de PyPack Studio
"""

import sys
import os
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets


class InstallWizard(QtWidgets.QWizard):
    def __init__(self):
        super().__init__()
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
        self.addPage(self.create_destination_page())
        self.addPage(self.create_components_page())
        self.addPage(self.create_summary_page())
        
        # Définir l'icône de la fenêtre
        if os.path.exists("pypack.ico"):
            self.setWindowIcon(QtGui.QIcon("pypack.ico"))
        elif os.path.exists("pypack.png"):
            self.setWindowIcon(QtGui.QIcon("pypack.png"))
        
        # Définir l'image de fond pour le côté gauche
        self.set_wizard_image()
        
        # Connecter le bouton "Installer" à la méthode d'installation
        self.button(QtWidgets.QWizard.FinishButton).clicked.connect(self.install_pypack)
    
    def set_wizard_image(self):
        # Dimensions recommandées pour l'image de gauche
        target_width = 280
        target_height = 270
        left_margin = 8  # Marge à gauche en pixels
        separator_width = 2  # Largeur du trait de séparation en pixels
        
        # Essayer de charger l'image
        image_path = None
        if os.path.exists("wizard.png"):
            image_path = "wizard.png"
        elif os.path.exists("projet.png"):
            image_path = "projet.png"
        elif os.path.exists("pypack.png"):
            image_path = "pypack.png"
        
        if image_path:
            pixmap = QtGui.QPixmap(image_path)
            if not pixmap.isNull():
                # Redimensionner l'image si elle est trop grande
                if pixmap.width() > target_width or pixmap.height() > target_height:
                    # Réduire la taille de l'image pour laisser de la place à la marge et au trait de séparation
                    scaled_width = target_width - left_margin - separator_width
                    pixmap = pixmap.scaled(scaled_width, target_height,
                                         QtCore.Qt.KeepAspectRatio,
                                         QtCore.Qt.SmoothTransformation)
                
                # Créer une nouvelle image avec une marge à gauche et un trait de séparation
                new_pixmap = QtGui.QPixmap(target_width, target_height)
                new_pixmap.fill(QtCore.Qt.transparent)  # Fond transparent
                
                # Dessiner le trait de séparation vertical
                painter = QtGui.QPainter(new_pixmap)
                painter.setPen(QtGui.QPen(QtCore.Qt.lightGray, separator_width))
                painter.drawLine(target_width - separator_width // 2, 0, target_width - separator_width // 2, target_height)
                
                # Dessiner l'image avec une marge à gauche
                painter.drawPixmap(left_margin, 0, pixmap)
                painter.end()
                
                self.setPixmap(QtWidgets.QWizard.WatermarkPixmap, new_pixmap)
            else:
                print(f"Erreur: Impossible de charger l'image {image_path}")
        else:
            print("Aucune image trouvée pour l'assistant")
    
    def create_intro_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle("Bienvenue dans l'assistant de création d'application PySide6")
        page.setSubTitle("Cet assistant va vous aider à créer une structure de base pour votre application.")
        
        # Ajouter une ligne de séparation horizontale juste après le sous-titre
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setLineWidth(1)
        # Ajouter une feuille de style pour rendre le séparateur plus visible
        separator.setStyleSheet("QFrame { color: #5a9bff; background: #5a9bff; }")
        # Définir la politique d'expansion pour prendre toute la largeur
        separator.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
        label = QtWidgets.QLabel(
            "Cette application va créer une structure de base pour une application PySide6 "
            "avec les éléments nécessaires pour commencer à développer.\n\n"
            "Cliquez sur Suivant pour continuer."
        )
        label.setWordWrap(True)
        
        layout = QtWidgets.QVBoxLayout(page)
        layout.setSpacing(0)  # Réduire l'espacement au minimum
        layout.addWidget(separator)
        layout.addWidget(label)
        
        return page
    
    def create_app_info_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle("Informations sur l'application")
        page.setSubTitle("Veuillez entrer les informations de base pour votre application.")
        
        # Nom de l'application
        name_label = QtWidgets.QLabel("Nom de l'application:")
        self.name_edit = QtWidgets.QLineEdit("MyApp")
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        
        # Description
        desc_label = QtWidgets.QLabel("Description:")
        self.desc_edit = QtWidgets.QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        desc_layout = QtWidgets.QVBoxLayout()
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)
        
        layout = QtWidgets.QVBoxLayout(page)
        layout.addLayout(name_layout)
        layout.addLayout(desc_layout)
        
        # Définir le champ comme requis
        page.registerField("app_name*", self.name_edit)
        
        return page
    
    def create_components_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle("Composants")
        page.setSubTitle("Sélectionnez les composants à inclure dans votre application.")
        
        # PySide6
        self.pyside_check = QtWidgets.QCheckBox("PySide6")
        self.pyside_check.setChecked(True)
        self.pyside_check.setEnabled(False)  # Toujours requis
        
        # Structure de base
        self.structure_check = QtWidgets.QCheckBox("Structure de base (main.py, resources, etc.)")
        self.structure_check.setChecked(True)
        self.structure_check.setEnabled(False)  # Toujours inclus
        
        # Fichier requirements.txt
        self.requirements_check = QtWidgets.QCheckBox("Fichier requirements.txt")
        self.requirements_check.setChecked(True)
        
        # Fichier de configuration PyInstaller
        self.pyinstaller_check = QtWidgets.QCheckBox("Fichier de configuration PyInstaller (.spec)")
        self.pyinstaller_check.setChecked(True)
        
        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(self.pyside_check)
        layout.addWidget(self.structure_check)
        layout.addWidget(self.requirements_check)
        layout.addWidget(self.pyinstaller_check)
        
        return page
    
    def create_destination_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle("Destination")
        page.setSubTitle("Choisissez le répertoire où créer votre application.")
        
        # Répertoire de destination
        dest_label = QtWidgets.QLabel("Répertoire de destination:")
        self.dest_edit = QtWidgets.QLineEdit()
        self.dest_edit.setText(str(Path.home() / "MyApp"))
        browse_btn = QtWidgets.QPushButton("Parcourir...")
        browse_btn.clicked.connect(self.browse_destination)
        
        dest_layout = QtWidgets.QHBoxLayout()
        dest_layout.addWidget(dest_label)
        dest_layout.addWidget(self.dest_edit)
        dest_layout.addWidget(browse_btn)
        
        layout = QtWidgets.QVBoxLayout(page)
        layout.addLayout(dest_layout)
        
        # Définir le champ comme requis
        page.registerField("dest_path*", self.dest_edit)
        
        return page
    
    def create_summary_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle("Résumé")
        page.setSubTitle("Voici un résumé de vos choix. Cliquez sur Terminer pour créer votre application.")
        
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
        # Mise à jour du résumé sur la dernière page
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
            # Créer le répertoire de destination
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Créer la structure de base
            if self.structure_check.isChecked():
                self.create_basic_structure(dest_path, app_name)
            
            # Créer le fichier requirements.txt
            if self.requirements_check.isChecked():
                self.create_requirements_file(dest_path)
            
            # Créer le fichier de configuration PyInstaller
            if self.pyinstaller_check.isChecked():
                self.create_pyinstaller_spec(dest_path, app_name)
            
            # Afficher un message de succès
            QtWidgets.QMessageBox.information(
                self, "Succès", 
                f"Le projet '{app_name}' a été créé avec succès dans:\n{dest_path}"
            )
            
        except Exception as e:
            # Afficher un message d'erreur
            QtWidgets.QMessageBox.critical(
                self, "Erreur", 
                f"Une erreur s'est produite lors de la création du projet:\n{str(e)}"
            )
    
    def create_basic_structure(self, dest_path, app_name):
        # Créer le script principal
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
        
        # Widget central
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Label de bienvenue
        label = QtWidgets.QLabel("Bienvenue dans {app_name}!")
        label.setAlignment(QtCore.Qt.AlignCenter)
        font = label.font()
        font.setPointSize(18)
        label.setFont(font)
        layout.addWidget(label)
        
        # Bouton de test
        button = QtWidgets.QPushButton("Cliquez-moi")
        button.clicked.connect(self.on_button_clicked)
        layout.addWidget(button)
        
        # Zone de texte
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setPlaceholderText("Entrez votre texte ici...")
        layout.addWidget(self.text_edit)
    
    def on_button_clicked(self):
        self.text_edit.append("Bonjour, monde!")


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
'''
        
        with open(dest_path / "main.py", "w", encoding="utf-8") as f:
            f.write(main_py_content)
        
        # Créer le répertoire des ressources
        resources_path = dest_path / "resources"
        resources_path.mkdir(exist_ok=True)
        
        # Créer un fichier README
        readme_content = f'''# {app_name}

## Description
{self.desc_edit.toPlainText()}

## Structure du projet
- `main.py`: Point d'entrée de l'application
- `resources/`: Répertoire pour les ressources (images, icônes, etc.)
- `requirements.txt`: Dépendances du projet
- `pypack.spec`: Fichier de configuration PyInstaller (si généré)

## Installation
1. Créez un environnement virtuel:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\\Scripts\\activate
   ```

2. Installez les dépendances:
   ```bash
   pip install -r requirements.txt
   ```

3. Exécutez l'application:
   ```bash
   python main.py
   ```

## Création d'un exécutable
Utilisez PyInstaller avec le fichier de configuration:
```bash
pyinstaller pypack.spec
```
'''
        
        with open(dest_path / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
    
    def create_requirements_file(self, dest_path):
        requirements_content = '''PySide6>=6.0.0
'''
        
        with open(dest_path / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content)
    
    def create_pyinstaller_spec(self, dest_path, app_name):
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

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
    icon='resources/icon.ico'  # Vous pouvez ajouter une icône ici
)
'''
        
        with open(dest_path / f"{app_name.lower()}.spec", "w", encoding="utf-8") as f:
            f.write(spec_content)


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Style
    app.setStyle("Fusion")
    
    # Style personnalisé
    app.setStyleSheet("""
    QMainWindow {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                    stop: 0 #2e2e2e, stop: 1 #1a1a1a);
        color: #ffffff;
    }
    
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
    
    QLineEdit, QTextEdit, QCheckBox, QWizardPage {
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
    """)
    
    wizard = InstallWizard()
    wizard.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()