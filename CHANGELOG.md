# 🟦 Changelog

---

## <span style="color:#005fa3; font-weight:bold;">1.3.0 · 2025-09-03</span>

### <span style="color:#007acc;">Nouveautés & UI</span>

- Amélioration visuelle de la liste des profils :
  - Icône devant chaque profil
  - Profil actif en bleu clair et gras
  - Police agrandie pour tous les profils
  - Effet survol moderne et cohérent avec le thème sombre
  - Sélection lumineuse et bordure bleue à gauche
- Ajout d’icônes aux boutons de la page Profils (Nouveau, Enregistrer, Supprimer, Exporter, Importer)
- Ajout d’icônes aux boutons de la page Projet (Analyser, Construire, Nettoyer)
- Couleurs et styles affinés pour une interface plus agréable

### <span style="color:#007acc;">Corrections</span>

- Correction de l’indentation et de l’utilisation de self dans ProfilesTabPage
- Correction du style hover pour qu’il soit en phase avec l’interface
- Correction de la sélection du profil actif après rafraîchissement

### <span style="color:#007acc;">Divers</span>

- Changelog et README mis à jour pour refléter les nouveautés
- Préparation pour de futures évolutions UX

---

## <span style="color:#005fa3; font-weight:bold;">1.2.0 · 2025-09-02</span>

### <span style="color:#007acc;">Nouveautés</span>

- Persistance complète de la case à cocher "Créer un setup après le build" dans les profils et la configuration.
- Synchronisation automatique de la visibilité de l’onglet Installation selon le profil chargé et la case à cocher.
- Correction de la gestion du type de retour de checkState() (conversion explicite en entier).
- Sauvegarde et restauration robustes des profils (QSettings, JSON export/import).
- Correction de bugs d’affichage et de synchronisation lors du changement de profil ou du rechargement de l’application.
- Amélioration de la logique de fallback pour le chargement des profils et de la configuration.
- Nettoyage et clarification du code de gestion des profils et de l’UI.

### <span style="color:#007acc;">Corrections</span>

- Correction du bug empêchant la case "Créer un setup après le build" d’être sauvegardée et restaurée.
- Correction du bug de visibilité de l’onglet Installation lors du changement de profil.
- Correction des erreurs liées au type Enum retourné par checkState().
- Correction de la sauvegarde dans le profil actif et le profil par défaut à la fermeture de l’application.

### <span style="color:#007acc;">Divers</span>

- Documentation et commentaires améliorés.
- Préparation pour de futures extensions (backends, options avancées).

---

## <span style="color:#005fa3; font-weight:bold;">1.1.0 · 2025-09-01</span>

### <span style="color:#007acc;">Nouveautés</span>

- Correction de la restitution des dossiers et fichiers à ajouter dans l’UI lors du chargement d’un profil ou d’une configuration.
- Suppression des références inutiles à tbl_data dans le code principal.
- Amélioration de la robustesse de la méthode _apply_config_to_ui (gestion des valeurs absentes ou None).
- Nettoyage du code et meilleure gestion des erreurs d’indentation et de portée.
- Icônes de navigation agrandies pour une meilleure visibilité.

### <span style="color:#007acc;">Corrections</span>

- Résolution des erreurs liées à des widgets non existants.
- Correction de la sauvegarde et de la restauration des champs directories_to_create et dirs_to_include.

### <span style="color:#007acc;">Divers</span>

- Documentation et commentaires améliorés pour faciliter la maintenance.
- Préparation pour de futures évolutions (ajout de nouveaux backends, options avancées).

---

## <span style="color:#005fa3; font-weight:bold;">1.0.0 · 2025-08-30</span>

### <span style="color:#007acc;">Ajouté</span>

- Style bleu pour les cases à cocher lorsqu'elles sont cochées
- Signal personnalisé pour la création du setup après le build

### <span style="color:#007acc;">Modifié</span>

- Refactorisation du code pour déporter la création du setup de BuildAction vers un signal/slot
- Correction des erreurs d'indentation dans le code

---

## <span style="color:#005fa3; font-weight:bold;">0.9.0 · 2025-08-29</span>

### <span style="color:#007acc;">Amélioré</span>

- Amélioration de la communication entre les composants pour l'arrêt du build
- Mise en place d'un signal personnalisé pour le bouton stop

---

## <span style="color:#005fa3; font-weight:bold;">0.8.0 · 2025-08-29</span>

### <span style="color:#007acc;">Ajouté</span>

- Page "Installation" avec un assistant d'installation pour créer une structure de base d'application PySide6
- Barre de progression pendant le processus de build
- Icônes personnalisées pour les onglets de l'interface
- Option dans la page "Projet" pour afficher le répertoire de sortie à la fin du build
- Sauvegarde et chargement de l'état de l'onglet sélectionné dans la barre latérale

### <span style="color:#007acc;">Amélioré</span>

- Gestion des fichiers et répertoires à copier dans le dossier de sortie
- Système de logs avec couleurs et icônes pour différents niveaux de messages
- Interface utilisateur avec des textes et des boutons plus explicites
- Persistance des paramètres utilisateur avec préfixe dans QSettings pour une meilleure organisation
- Navigation automatique vers l'onglet "Sortie & Logs" lors du lancement d'un build, avec sélection de l'onglet dans la barre latérale

### <span style="color:#007acc;">Corrigé</span>

- Correction de l'erreur AttributeError: 'OutputTabPage' object has no attribute '_config_from_ui' lors de la fin d'un build
- Correction de l'agencement de l'interface utilisateur de l'onglet "Output" pour que le bouton "Stop" apparaisse en bas
- Correction de la logique d'arrêt du build pour que le bouton "Stop" fonctionne correctement

---

## <span style="color:#005fa3; font-weight:bold;">0.7.0 · 2025-08-28</span>

### <span style="color:#007acc;">Corrigé</span>

- Correction de l'erreur AttributeError: 'OutputTabPage' object has no attribute '_config_from_ui' lors de la fin d'un build
- Correction de l'agencement de l'interface utilisateur de l'onglet "Output" pour que le bouton "Stop" apparaisse en bas
- Correction de la logique d'arrêt du build pour que le bouton "Stop" fonctionne correctement

---

## <span style="color:#005fa3; font-weight:bold;">0.6.0 · 2025-08-27</span>

### <span style="color:#007acc;">Ajouté</span>

- Option dans la page "Projet" pour afficher le répertoire de sortie à la fin du build
- Sauvegarde et chargement de l'état de l'onglet sélectionné dans la barre latérale

### <span style="color:#007acc;">Amélioré</span>

- Persistance des paramètres utilisateur avec préfixe dans QSettings pour une meilleure organisation
- Navigation automatique vers l'onglet "Sortie & Logs" lors du lancement d'un build, avec sélection de l'onglet dans la barre latérale

---

## <span style="color:#005fa3; font-weight:bold;">0.5.5 · 2025-08-27</span>

- Gestion améliorée des dossiers pour la distribution

---

## <span style="color:#005fa3; font-weight:bold;">0.5.0 · 2025-08-27</span>

- Ajout de répertoires pour mieux structurer l'ensemble du projet
- Ensemble plus modulaire et plus facile à maintenir

---

## <span style="color:#005fa3; font-weight:bold;">0.4.0 · 2025-08-26</span>

### <span style="color:#007acc;">Ajouté</span>

- Assistant d'installation pour créer une structure de base d'application PySide6
- Possibilité de copier des fichiers et répertoires dans le dossier de sortie après le build
- Barre de progression pendant le processus de build

---

## <span style="color:#005fa3; font-weight:bold;">0.3.0 · 2025-08-24</span>

### <span style="color:#007acc;">Modifié</span>

- Refactorisation du code : déplacement des classes backend dans un fichier séparé

---

## <span style="color:#005fa3; font-weight:bold;">0.2.0 · 2025-08-23</span>

### <span style="color:#007acc;">Ajouté</span>

- Copie automatique de fichiers et répertoires dans le dossier de sortie
- Support des icônes d'application pour Windows

### <span style="color:#007acc;">Corrigé</span>

- Problèmes de compatibilité avec les chemins Windows
- Erreurs lors de la copie de fichiers et répertoires

---

## <span style="color:#005fa3; font-weight:bold;">0.1.0 · 2025-08-23</span>

### <span style="color:#007acc;">Ajouté</span>

- Interface utilisateur avec PySide6 pour la configuration du packaging
- Support de deux backends d'empaquetage : PyInstaller et Nuitka
- Gestion des profils de build persistés avec export/import JSON
- Validation de formulaire et normalisation des chemins
- Détection automatique de l'environnement virtuel
- Journalisation en mémoire avec export
- Assistant d'installation pour créer une structure de base d'application PySide6

### <span style="color:#007acc;">Modifié</span>

- Amélioration de l'interface utilisateur avec un design personnalisé
- Optimisation du processus de build avec exécution non bloquante via QProcess
- Mise à jour de la documentation avec des instructions détaillées

---
