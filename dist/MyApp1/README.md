# MyApp1

## Description


## Structure du projet
- `main.py`: Point d'entrée de l'application
- `resources/`: Répertoire pour les ressources
- `requirements.txt`: Dépendances du projet
- `pypack.spec`: Fichier de configuration PyInstaller

## Installation
1. Créez un environnement virtuel:
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate

2. Installez les dépendances:
   pip install -r requirements.txt

3. Exécutez l'application:
   python main.py

## Création d'un exécutable
pyinstaller pypack.spec
