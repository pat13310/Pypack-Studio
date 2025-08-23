"""
Script de test pour l'assistant d'installation.
"""

import sys
from pathlib import Path
from PySide6 import QtWidgets
from install_wizard import InstallWizard

def test_install():
    """Teste l'installation en appelant directement create_project."""
    app = QtWidgets.QApplication(sys.argv)
    
    # Créer une instance de l'assistant
    wizard = InstallWizard()
    
    # Simuler le remplissage des champs requis
    wizard.setField("app_name", "MyApp")
    wizard.setField("dest_path", "C:\\temp\\TestApp")
    
    # Appeler la méthode de création de projet
    wizard.create_project()

if __name__ == "__main__":
    test_install()