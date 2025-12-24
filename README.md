# Zero Trust Multimodal Biometric System - Proof of Concept

Ce projet implémente un système de sécurité biométrique basé sur le **Zero Trust** et la **Biométrie Révocable (BioHashing)**. 

L'objectif est de prouver qu'il est possible d'authentifier un utilisateur sans jamais stocker ses données biométriques brutes (photos de visage ou empreintes), tout en permettant la révocation des accès en cas de compromission.

## 📌 Fonctionnement (Théorie)

Le cœur du système repose sur l'algorithme de **BioHashing** :

1.  **Extraction de Caractéristiques** : On extrait un vecteur unique (128 dimensions) du visage de l'utilisateur.
2.  **Génération de Token (Seed)** : Chaque utilisateur possède un "Token" secret (ex: un nombre aléatoire ou un mot de passe).
3.  **Projection Aléatoire** : 
    *   Le Token sert à générer une matrice aléatoire unique.
    *   Les caractéristiques du visage sont projetées (multipliées) par cette matrice.
    *   Cela "mélange" la biométrie avec le secret de manière irréversible.
4.  **Binarisation** : Le résultat est transformé en une suite de 0 et de 1 (le BioHash).

### Avantages
*   **Révocabilité** : Si le BioHash est volé, il suffit de changer le Token pour générer un NOUVEAU BioHash valide (comme changer un mot de passe).
*   **Protection de la Vie Privée** : Impossible de retrouver le visage d'origine à partir du BioHash.
*   **Zero Trust** : L'accès nécessite "Ce que je suis" (Visage) + "Ce que je possède" (Token).

---

## 🛠️ Installation

### Prérequis
*   Python 3.x
*   Environnement Linux (recommandé)

### 1. Installation des dépendances
Nous utilisons un environnement virtuel pour isoler les paquets.

```bash
# Aller dans le dossier du projet
cd "/home/red/Documents/S5/Biom Sec/Project/"

# Créer l'environnement virtuel
python3 -m venv venv

# Installer les dépendances
./venv/bin/pip install -r requirements.txt
```

### 2. Téléchargement des Modèles (Dlib)
Le script a besoin des modèles de prédiction de visage de Dlib. S'ils ne sont pas présents, téléchargez-les :

```bash
# Télécharger et extraire les modèles
wget -c http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
wget -c http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2

bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
bzip2 -d dlib_face_recognition_resnet_model_v1.dat.bz2
```

---

## 🚀 Utilisation (Proof of Concept)

Le script `biohashing_poc.py` permet de tester la comparaison entre deux images avec des clés (seeds) spécifiques.

### Commande de base
```bash
./venv/bin/python biohashing_poc.py --img1 "chemin/image1.jpg" --img2 "chemin/image2.jpg" --seed1 [TOKEN1] --seed2 [TOKEN2]
```

### Scénarios de Test

#### 1. Accès Valide (Même personne, Même clé)
```bash
./venv/bin/python biohashing_poc.py \
  --img1 "person_a.png" \
  --img2 "person_a.png" \
  --seed1 42 --seed2 42
```
✅ **Résultat attendu :** MATCH ACCEPTED (Distance ≈ 0.0)

#### 2. Attaque d'Imposteur (Personnes différentes, Même clé)
```bash
./venv/bin/python biohashing_poc.py \
  --img1 "person_a.png" \
  --img2 "person_b.png" \
  --seed1 42 --seed2 42
```
❌ **Résultat attendu :** MATCH REJECTED (Distance > 0.15)

#### 3. Révocation (Même personne, Clé compromise changée)
```bash
./venv/bin/python biohashing_poc.py \
  --img1 "person_a.png" \
  --img2 "person_a.png" \
  --seed1 42 --seed2 999
```
❌ **Résultat attendu :** MATCH REJECTED (Distance ≈ 0.5)
*Ceci prouve que sans la bonne clé, le visage seul ne suffit pas.*

---

## 📂 Structure du Projet (Phase 1)
*   `biohashing_poc.py` : Script principal contenant la logique de BioHashing.
*   `requirements.txt` : Liste des librairies Python nécessaires.
*   `*.dat` : Modèles de Machine Learning pour la reconnaissance faciale (Dlib).

---

## 🏛️ Phase 2 : API Backend (Core System)

Le projet expose désormais une API REST (FastAPI) pour l'intégration.

### Lancement du Serveur
```bash
./venv/bin/uvicorn backend.main:app --reload
```
Le serveur sera accessible sur `http://127.0.0.1:8000`.
La documentation interactive (Swagger UI) est disponible sur `http://127.0.0.1:8000/docs`.

### Endpoints Principaux

#### 1. Enrôlement (`POST /auth/enroll`)
Enregistre un nouvel utilisateur et son BioHash (sans stocker l'image).
*   **Champs** : `username` (string), `file` (image upload).
*   **Réponse** : ID utilisateur et confirmation.

#### 2. Vérification (`POST /auth/verify`)
Vérifie l'identité d'un utilisateur.
*   **Champs** : `username` (string), `file` (image upload).
*   **Réponse** : `authenticated` (bool), `message`.

### Test Automatisé
Un script de test est fourni pour valider le fonctionnement :
```bash
./venv/bin/python backend/test_phase2.py
```
Il simule un enrôlement, une connexion valide, et une tentative d'usurpation.
