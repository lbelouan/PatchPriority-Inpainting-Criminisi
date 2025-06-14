# Création du mask + Inpainting

Une application Python moderne et interactive pour créer des masques binaires à partir d'images, puis appliquer un inpainting avancé (Criminisi), avec une interface graphique professionnelle, précise et agréable à utiliser.

---

## Sommaire
- [Fonctionnalités](#fonctionnalités)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Modes de sélection](#modes-de-sélection)
- [Inpainting et patch](#inpainting-et-patch)
- [KPI et statistiques](#kpi-et-statistiques)
- [Navigation et zoom](#navigation-et-zoom)
- [Raccourcis et astuces](#raccourcis-et-astuces)
- [Dépendances](#dépendances)
- [FAQ](#faq)
- [Auteur](#auteur)

---

## Fonctionnalités

- **Interface moderne et épurée** (Tkinter, style web-app)
- **Chargement d'images** depuis le disque
- **Deux modes de sélection** :
  - **Dessin continu** (tracé libre à la souris)
  - **Polygone par points** (clics successifs)
- **Zoom** avec la molette de la souris pour une annotation précise
- **Déplacement de la vue** (scrollbars, clic droit)
- **Fermeture automatique du masque**
- **Annulation du dernier point** (mode polygone)
- **Effacement de la sélection**
- **Sauvegarde du masque** au format PNG
- **Ajustement dynamique** : le masque et les points restent alignés même après zoom ou déplacement
- **Inpainting avancé (Criminisi)** avec :
  - Aperçu temps réel (progression patch par patch)
  - Téléchargement de l'image inpaintée
  - Gestion automatique ou manuelle de la taille du patch
- **KPI/statistiques** :
  - Temps d'exécution total
  - Taux de pixels remplis
  - Nombre d'itérations
- **Bouton Reset** pour tout réinitialiser (image, masque, stats, interface)

---

## Installation

1. Assurez-vous d'avoir Python 3.7+ installé
2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

---

## Utilisation

1. Lancez l'application :
```bash
python main.py
```

2. Utilisez les boutons de l'interface :
   - **Charger Image** : Sélectionnez une image à annoter
   - **Effacer Sélection** : Recommencez la sélection
   - **Valider le masque** : Validez la zone à inpaint
   - **Télécharger le masque** : Enregistrez le masque généré
   - **Inpainting** : Lancez l'inpainting sur la zone masquée
   - **Reset** (en haut à droite) : Réinitialise tout pour repartir de zéro

3. Pour créer un masque :
   - **Mode Dessin continu** :
     - Cliquez et faites glisser la souris pour dessiner la région d'intérêt
     - Relâchez pour fermer automatiquement le masque
   - **Mode Polygone par points** :
     - Cliquez pour placer chaque sommet
     - Le masque sera toujours fermé à l'export
     - Utilisez "Retour" pour annuler le dernier point

4. **Taille du patch (inpainting)** :
   - Choisissez entre **Automatique** (patch = 21) ou **Manuel** (entrez un impair positif ≤ 50% de la largeur de l'image)
   - Un message d'erreur s'affiche si la valeur n'est pas valide

5. **Inpainting** :
   - Cliquez sur "Inpainting" après validation du masque
   - Suivez la progression en temps réel dans la fenêtre dédiée
   - Téléchargez le résultat final si souhaité

6. **KPI/statistiques** :
   - Temps d'exécution, taux de pixels remplis, nombre d'itérations affichés à droite

---

## Modes de sélection

- **Dessin continu** :
  - Idéal pour des contours libres et rapides
  - Le masque se ferme automatiquement à la fin du tracé
- **Polygone par points** :
  - Idéal pour des contours précis, point par point
  - Le masque est toujours fermé à l'export
  - Utilisez "Retour" pour corriger un point

---

## Inpainting et patch

- **Inpainting Criminisi** :
  - L'algorithme comble la zone masquée de façon réaliste
  - Aperçu temps réel de la progression
  - Téléchargement de l'image inpaintée possible
- **Taille du patch** :
  - **Automatique** : patch = 21 (recommandé pour la plupart des cas)
  - **Manuel** : entrez un impair positif ≤ 50% de la largeur de l'image
  - Un message d'erreur s'affiche si la valeur n'est pas valide

---

## KPI et statistiques

- **Temps d'exécution total** de l'inpainting (en secondes)
- **Taux de pixels remplis** (pourcentage de la zone masquée)
- **Nombre d'itérations** (nombre de patchs traités)
- Affichage en temps réel et à la fin de l'inpainting

---

## Navigation et zoom

- **Zoom** :
  - Molette de la souris vers le haut : zoom avant
  - Molette de la souris vers le bas : zoom arrière
- **Déplacement** :
  - Scrollbars horizontale et verticale
  - Clic droit maintenu + déplacement souris : déplacement libre ("main")
- **Ajustement automatique** :
  - Les points et le masque restent alignés avec l'image, même après zoom ou déplacement

---

## Raccourcis et astuces

- Molette : zoom
- Clic droit maintenu : déplacement
- "Retour" : annuler le dernier point (mode polygone)
- Vous pouvez zoomer à tout moment, même en cours de tracé
- Le masque suit toujours l'image, même après un zoom ou un déplacement
- Le mode polygone permet une annotation très précise, point par point
- Le bouton Reset permet de repartir de zéro à tout moment

---

## Dépendances

- OpenCV
- NumPy
- Pillow
- Tkinter (inclus dans Python)

---

## FAQ

**Q : Le masque ne suit pas l'image quand je zoome ?**
R : Les points sont recalculés à chaque zoom/déplacement, assurez-vous d'utiliser la dernière version du code.

**Q : Comment annoter précisément une petite zone ?**
R : Zoomez avec la molette, déplacez la vue avec le clic droit ou les scrollbars, puis placez vos points.

**Q : Puis-je annuler un point en mode continu ?**
R : Non, l'annulation n'est disponible qu'en mode polygone.

**Q : Le masque est-il toujours fermé ?**
R : Oui, il est automatiquement fermé à l'export, même si vous n'avez pas relié le dernier point au premier.

**Q : Puis-je utiliser ce programme sur Mac/Linux/Windows ?**
R : Oui, il fonctionne sur tous les systèmes avec Python 3 et les dépendances installées.

---

## Auteur

Développé par LE BIZEC Elouan et Cheikh Yanis — 2025 