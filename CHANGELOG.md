# 🟦 Changelog

---

## <span style="color:#007acc">1.2.0</span> · 2025-09-02

### ✨ Nouveautés

- Persistance complète de la case à cocher "Créer un setup après le build" dans les profils et la configuration.
- Synchronisation automatique de la visibilité de l’onglet Installation selon le profil chargé et la case à cocher.
- Correction de la gestion du type de retour de `checkState()` (conversion explicite en entier).
- Sauvegarde et restauration robustes des profils (QSettings, JSON export/import).
- Correction de bugs d’affichage et de synchronisation lors du changement de profil ou du rechargement de l’application.
- Amélioration de la logique de fallback pour le chargement des profils et de la configuration.
- Nettoyage et clarification du code de gestion des profils et de l’UI.

### 🛠 Corrections

- Correction du bug empêchant la case "Créer un setup après le build" d’être sauvegardée et restaurée.
- Correction du bug de visibilité de l’onglet Installation lors du changement de profil.
- Correction des erreurs liées au type Enum retourné par `checkState()`.
- Correction de la sauvegarde dans le profil actif et le profil par défaut à la fermeture de l’application.

### 📚 Divers

- Documentation et commentaires améliorés.
- Préparation pour de futures extensions (backends, options avancées).

---

## <span style="color:#007acc">1.1.0</span> · 2025-09-01

### ✨ Nouveautés

- Correction de la restitution des dossiers et fichiers à ajouter dans l’UI lors du chargement d’un profil ou d’une configuration.
- Suppression des références inutiles à `tbl_data` dans le code principal.
- Amélioration de la robustesse de la méthode `_apply_config_to_ui` (gestion des valeurs absentes ou None).
- Nettoyage du code et meilleure gestion des erreurs d’indentation et de portée.
- Icônes de navigation agrandies pour une meilleure visibilité.

### 🛠 Corrections

- Résolution des erreurs liées à des widgets non existants.
- Correction de la sauvegarde et de la restauration des champs `directories_to_create` et `dirs_to_include`.

### 📚 Divers

- Documentation et commentaires améliorés pour faciliter la maintenance.
- Préparation pour de futures évolutions (ajout de nouveaux backends, options avancées).

---

## <span style="color:#007acc">1.0.0</span> · 2025-08-30

### ✨ Ajouté

- Style bleu pour les cases à cocher lorsqu'elles sont cochées
- Signal personnalisé pour la création du setup après le build

### 🔄 Modifié

- Refactorisation du code pour déporter la création du setup de BuildAction vers un signal/slot
- Correction des erreurs d'indentation dans le code

---

## <span style="color:#007acc">0.9.0</span> · 2025-08-29

### 🚀 Amélioré

- Amélioration de la communication entre les composants pour l'arrêt du build
- Mise en place d'un signal personnalisé pour le bouton stop

---

## <span style="color:#007acc">0.8.0</span> · 2025-08-29

### ✨ Ajouté

- Page "Installation" avec un assistant d'installation pour créer une structure de base d'application PySide6
- Barre de progression pendant le processus de build
- Icônes personnalisées pour les onglets de l'interface
- Option dans la page "Projet" pour afficher le répertoire de sortie à la fin du build
- Sauvegarde et chargement de l'état de l'onglet sélectionné dans la barre latérale

### 🚀 Amélioré

- Gestion des fichiers et répertoires à copier dans le dossier de sortie
- Système de logs avec couleurs et icônes pour différents niveaux de messages
- Interface utilisateur avec des textes et des boutons plus explicites
- Persistance des paramètres utilisateur avec préfixe dans QSettings pour une meilleure organisation
- Navigation automatique vers l'onglet "Sortie & Logs" lors du lancement d'un build, avec sélection de l'onglet dans la barre latérale

### 🛠 Corrigé

- Correction de l'erreur `AttributeError: 'OutputTabPage' object has no attribute '_config_from_ui'` lors de la fin d'un build
- Correction de l'agencement de l'interface utilisateur de l'onglet "Output" pour que le bouton "Stop" apparaisse en bas
- Correction de la logique d'arrêt du build pour que le bouton "Stop" fonctionne correctement

---

## <span style="color:#007acc">0.7.0</span> · 2025-08-28

### 🛠 Corrigé

- Correction de l'erreur `AttributeError: 'OutputTabPage' object has no attribute '_config_from_ui'` lors de la fin d'un build
- Correction de l'agencement de l'interface utilisateur de l'onglet "Output" pour que le bouton "Stop" apparaisse en bas
- Correction de la logique d'arrêt du build pour que le bouton "Stop" fonctionne correctement

---

## <span style="color:#007acc">0.6.0</span> · 2025-08-27

### ✨ Ajouté

- Option dans la page "Projet" pour afficher le répertoire de sortie à la fin du build
- Sauvegarde et chargement de l'état de l'onglet sélectionné dans la barre latérale

### 🚀 Amélioré

- Persistance des paramètres utilisateur avec préfixe dans QSettings pour une meilleure organisation
- Navigation automatique vers l'onglet "Sortie & Logs" lors du lancement d'un build, avec sélection de l'onglet dans la barre latérale

---

## <span style="color:#007acc">0.5.5</span> · 2025-08-27

- Gestion améliorée des dossiers pour la distribution

---

## <span style="color:#007acc">0.5.0</span> · 2025-08-27

- Ajout de répertoires pour mieux structurer l'ensemble du projet
- Ensemble plus modulaire et plus facile à maintenir

---

## <span style="color:#007acc">0.4.0</span> · 2025-08-26

### ✨ Ajouté

- Assistant d'installation pour créer une structure de base d'application PySide6
- Possibilité de copier des fichiers et répertoires dans le dossier de sortie après le build
- Barre de progression pendant le processus de build
- Icônes personnalisées pour les onglets de l'interface

### 🚀 Amélioré

- Système de logs avec couleurs et icônes pour différents niveaux de messages
- Interface utilisateur avec des textes et des boutons plus explicites

---

## <span style="color:#007acc">0.3.0</span> · 2025-08-24

### 🔄 Modifié

- Refactorisation du code : déplacement des classes backend dans un fichier séparé

---

## <span style="color:#007acc">0.2.0</span> · 2025-08-23

### ✨ Ajouté

- Copie automatique de fichiers et répertoires dans le dossier de sortie
- Support des icônes d'application pour Windows

### 🛠 Corrigé

- Problèmes de compatibilité avec les chemins Windows
- Erreurs lors de la copie de fichiers et répertoires

---

## <span style="color:#007acc">0.1.0</span> · 2025-08-23

### ✨ Ajouté

- Interface utilisateur avec PySide6 pour la configuration du packaging
- Support de deux backends d'empaquetage : PyInstaller et Nuitka
- Gestion des profils de build persistés avec export/import JSON
- Validation de formulaire et normalisation des chemins
- Détection automatique de l'environnement virtuel
- Journalisation en mémoire avec export
- Assistant d'installation pour créer une structure de base d'application PySide6

### 🔄 Modifié

- Amélioration de l'interface utilisateur avec un design personnalisé
- Optimisation du processus de build avec exécution non bloquante via QProcess
- Mise à jour de la documentation avec des instructions détaillées

---
