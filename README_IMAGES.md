# Guide pour les images de l'assistant d'installation

## Format recommandé

Les images utilisées dans l'assistant d'installation doivent être au format **PNG avec transparence** pour assurer un affichage correct.

## Dimensions recommandées

- **Largeur :** 1024 pixels
- **Hauteur :** 1024 pixels

Ces dimensions permettent un bon redimensionnement dans l'assistant d'installation sans perte de qualité.

## Création d'images avec transparence

### Outils recommandés

1. **GIMP** (gratuit et open-source)
   - Téléchargement : https://www.gimp.org/downloads/
   - Pour créer une image avec transparence :
     1. Fichier → Nouveau
     2. Dans la boîte de dialogue, sélectionner "Transparence" comme couleur d'arrière-plan
     3. Créer votre image
     4. Fichier → Exporter → Choisir le format PNG
     5. Dans les options d'exportation, cocher "Enregistrer la transparence"

2. **Adobe Photoshop** (payant)
   - Pour créer une image avec transparence :
     1. Fichier → Nouveau
     2. Dans la boîte de dialogue, sélectionner "Transparent" comme couleur d'arrière-plan
     3. Créer votre image
     4. Fichier → Enregistrer sous → Choisir le format PNG
     5. Dans les options, cocher "Transparence"

3. **Paint.NET** (gratuit)
   - Téléchargement : https://www.getpaint.net/
   - Pour créer une image avec transparence :
     1. Fichier → Nouveau
     2. Sélectionner "Transparent" comme type de calque
     3. Créer votre image
     4. Fichier → Enregistrer sous → Choisir le format PNG

## Bonnes pratiques

1. **Zone de contenu** :
   - Placez le contenu principal de votre image dans une zone centrale
   - Laissez des marges pour le redimensionnement automatique

2. **Transparence** :
   - Utilisez la transparence pour créer des formes ou logos qui s'intègrent bien avec l'interface
   - Évitez les images avec fond blanc sauf si c'est intentionnel

3. **Couleurs** :
   - Utilisez des couleurs qui contrastent bien avec l'interface sombre de l'assistant
   - Évitez les couleurs trop proches du gris foncé utilisé dans l'interface

4. **Texte** :
   - Évitez d'inclure du texte dans les images, car cela ne s'adapte pas bien aux différentes tailles
   - Si du texte est nécessaire, utilisez des polices vectorielles

## Fichiers d'image utilisés

- `installation.png` : Image principale de l'assistant d'installation
- `wizard.png` : Image de secours pour l'assistant
- `projet.png` : Image utilisée si les autres ne sont pas disponibles
- `pypack.png` : Image par défaut de l'application

## Problèmes courants

1. **Image avec fond noir** :
   - Vérifiez que l'image est bien au format PNG avec transparence
   - Vérifiez que le canal alpha est préservé lors de l'enregistrement

2. **Mauvaise qualité** :
   - Utilisez des dimensions suffisantes (1024x1024 recommandé)
   - Évitez le redimensionnement excessif

3. **Image non affichée** :
   - Vérifiez que le fichier existe dans le répertoire de l'application
   - Vérifiez que le nom du fichier correspond exactement (sensible à la casse)

## Test de l'image

Pour tester si votre image a une transparence correcte, vous pouvez utiliser le script Python suivant :

```python
from PySide6 import QtGui
import sys

app = QtGui.QGuiApplication(sys.argv)

# Remplacer 'votre_image.png' par le chemin de votre image
pixmap = QtGui.QPixmap('votre_image.png')

print(f"Taille de l'image : {pixmap.width()}x{pixmap.height()}")
print(f"Image valide : {not pixmap.isNull()}")
print(f"Image avec transparence : {pixmap.hasAlpha()}")
```

Ce script affichera les informations sur votre image et vous indiquera si elle a un canal alpha (transparence).