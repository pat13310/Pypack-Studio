# Changelog

Toutes les modifications notables apportées à ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
et ce projet adhère au [Versionnage Sémantique](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-08-26

### Ajouté
- Assistant d'installation pour créer une structure de base d'application PySide6
- Possibilité de copier des fichiers et répertoires dans le dossier de sortie après le build
- Barre de progression pendant le processus de build
- Icônes personnalisées pour les onglets de l'interface

### Amélioré
- Système de logs avec couleurs et icônes pour différents niveaux de messages
- Interface utilisateur avec des textes et des boutons plus explicites

## [0.3.0] - 2025-08-24

### Modifié
- Refactorisation du code : déplacement des classes backend dans un fichier séparé

## [0.2.0] - 2025-08-23

### Ajouté
- Copie automatique de fichiers et répertoires dans le dossier de sortie
- Support des icônes d'application pour Windows

### Corrigé
- Problèmes de compatibilité avec les chemins Windows
- Erreurs lors de la copie de fichiers et répertoires

## [0.1.0] - 2025-08-23

### Ajouté
- Interface utilisateur avec PySide6 pour la configuration du packaging
- Support de deux backends d'empaquetage : PyInstaller et Nuitka
- Gestion des profils de build persistés avec export/import JSON
- Validation de formulaire et normalisation des chemins
- Détection automatique de l'environnement virtuel
- Journalisation en mémoire avec export
- Assistant d'installation pour créer une structure de base d'application PySide6

### Modifié
- Amélioration de l'interface utilisateur avec un design personnalisé
- Optimisation du processus de build avec exécution non bloquante via QProcess
- Mise à jour de la documentation avec des instructions détaillées

[0.1.0]: https://github.com/pat13310/Pypack-Studio/releases/tag/v0.1.0
[0.2.0]: https://github.com/pat13310/Pypack-Studio/compare/v0.1.0...v0.2.0
[0.3.0]: https://github.com/pat13310/Pypack-Studio/compare/v0.2.0...v0.3.0
[0.4.0]: https://github.com/pat13310/Pypack-Studio/compare/v0.3.0...v0.4.0