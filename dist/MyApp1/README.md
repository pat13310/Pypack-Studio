# MyApp1

## Description


## Structure du projet
- `main.py`: Point d'entrée de l'application
- `resources/`: Répertoire pour les ressources (images, icônes, etc.)
- `requirements.txt`: Dépendances du projet
- `pypack.spec`: Fichier de configuration PyInstaller (si généré)

## Installation
1. Créez un environnement virtuel:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
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
