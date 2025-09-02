# Pypack Studio

<img width="1929" height="1489" alt="image" src="https://github.com/user-attachments/assets/207d76fc-bae8-4500-bd0a-d20f1db36dc3" />

---

## Présentation

**Pypack Studio** est un outil moderne et convivial pour créer des exécutables Python professionnels, avec une interface graphique élégante basée sur PySide6. Il facilite le packaging, la gestion des profils, et l’automatisation du build pour vos applications.

---

## Fonctionnalités principales

- 🖥️ Interface graphique intuitive (Qt Widgets)
- 📦 Packaging avec PyInstaller et Nuitka
- 🔄 Profils de build persistents (QSettings, export/import JSON)
- 🛠️ Assistant d’installation et création de setup
- 📁 Gestion avancée des fichiers et répertoires à inclure
- 📝 Logs en temps réel et exportables
- 🎨 Personnalisation des icônes et ressources
- ✅ Validation des champs et détection automatique de venv

---

## Installation rapide

1. **Créez un environnement virtuel**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Installez les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Lancez l’application**
   ```bash
   python main.py
   ```

---

## Générer un exécutable

Utilisez PyInstaller avec le fichier de configuration fourni :
```bash
pyinstaller pypack.spec
```

---

## Ressources
- [Documentation PyInstaller](https://pyinstaller.org/)
- [Documentation Nuitka](https://nuitka.net/)
- [Qt for Python (PySide6)](https://doc.qt.io/qtforpython/)

---

## Support & Contribuer

Pour toute suggestion, bug ou contribution, ouvrez une issue sur le dépôt GitHub ou contactez le mainteneur.

---
