# Changelog

Toutes les modifications notables apportées à ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
et ce projet adhère au [Versionnage Sémantique](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2025-08-29

### Amélioré
- Amélioration de la communication entre les composants pour l'arrêt du build
- Mise en place d'un signal personnalisé pour le bouton stop

## [0.8.0] - 2025-08-29

### Ajouté
- Page "Installation" avec un assistant d'installation pour créer une structure de base d'application PySide6
- Barre de progression pendant le processus de build
- Icônes personnalisées pour les onglets de l'interface
- Option dans la page "Projet" pour afficher le répertoire de sortie à la fin du build
- Sauvegarde et chargement de l'état de l'onglet sélectionné dans la barre latérale

### Amélioré
- Gestion des fichiers et répertoires à copier dans le dossier de sortie
- Système de logs avec couleurs et icônes pour différents niveaux de messages
- Interface utilisateur avec des textes et des boutons plus explicites
- Persistance des paramètres utilisateur avec préfixe dans QSettings pour une meilleure organisation
- Navigation automatique vers l'onglet "Sortie & Logs" lors du lancement d'un build, avec sélection de l'onglet dans la barre latérale

### Corrigé
- Correction de l'erreur `AttributeError: 'OutputTabPage' object has no attribute '_config_from_ui'` lors de la fin d'un build
- Correction de l'agencement de l'interface utilisateur de l'onglet "Output" pour que le bouton "Stop" apparaisse en bas
- Correction de la logique d'arrêt du build pour que le bouton "Stop" fonctionne correctement

[0.8.0]: https://github.com/pat13310/Pypack-Studio/compare/v0.7.0...v0.8.0

## [0.7.0] - 2025-08-28

### Corrigé
- Correction de l'erreur `AttributeError: 'OutputTabPage' object has no attribute '_config_from_ui'` lors de la fin d'un build
- Correction de l'agencement de l'interface utilisateur de l'onglet "Output" pour que le bouton "Stop" apparaisse en bas
- Correction de la logique d'arrêt du build pour que le bouton "Stop" fonctionne correctement



## [0.6.0] - 2025-08-27

### Ajouté
- Option dans la page "Projet" pour afficher le répertoire de sortie à la fin du build
- Sauvegarde et chargement de l'état de l'onglet sélectionné dans la barre latérale

### Amélioré
- Persistance des paramètres utilisateur avec préfixe dans QSettings pour une meilleure organisation
- Navigation automatique vers l'onglet "Sortie & Logs" lors du lancement d'un build, avec sélection de l'onglet dans la barre latérale



## [0.5.5] - 2025-08-27
- Gestion améliorée des dossiers pour la distribution



## [0.5.0] - 2025-08-27
- Ajout de répertoires pour mieux structurer l'ensemble du projet
- Ensemble plus modulaire et plus facile à maintenir

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
[0.5.0]: https://github.com/pat13310/Pypack-Studio/compare/v0.4.0...v0.5.0
[0.5.5]: https://github.com/pat13310/Pypack-Studio/compare/v0.5.0...v0.5.5
[0.6.0]: https://github.com/pat13310/Pypack-Studio/compare/v0.5.5...v0.6.0
[0.7.0]: https://github.com/pat13310/Pypack-Studio/compare/v0.6.0...v0.7.0
