# Changelog

Toutes les modifications notables apportées à ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
et ce projet adhère au [Versionnage Sémantique](https://semver.org/spec/v2.0.0.html).

## [Non publié]

### Ajouté
- Interface utilisateur avec PySide6 pour la configuration du packaging
- Support de deux backends d'empaquetage : PyInstaller et Nuitka
- Gestion des profils de build persistés avec export/import JSON
- Validation de formulaire et normalisation des chemins
- Détection automatique de l'environnement virtuel
- Journalisation en mémoire avec export
- Assistant d'installation pour créer une structure de base d'application PySide6
- Copie automatique de fichiers et répertoires dans le dossier de sortie
- Support des icônes d'application pour Windows

### Modifié
- Amélioration de l'interface utilisateur avec un design personnalisé
- Optimisation du processus de build avec exécution non bloquante via QProcess
- Mise à jour de la documentation avec des instructions détaillées

### Corrigé
- Problèmes de compatibilité avec les chemins Windows
- Erreurs lors de la copie de fichiers et répertoires

## [1.0.0] - 2025-08-23

### Ajouté
- Version initiale de PyPack Studio
- Interface graphique complète avec onglets pour la configuration du projet
- Support de base pour PyInstaller et Nuitka
- Fonctionnalité de profil pour sauvegarder les configurations
- Système de journalisation des builds
- Assistant d'installation pour créer de nouvelles applications PySide6

[Non publié]: https://github.com/pat13310/Pypack-Studio/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/pat13310/Pypack-Studio/releases/tag/v1.0.0