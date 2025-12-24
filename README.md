# Zero Trust Multimodal Biometric System 🛡️

Ce projet implémente un système d'authentification biométrique ultra-sécurisé combinant **Reconnaissance Faciale**, **Empreintes Digitales** et **Architecture Zero Trust**.

## 🚀 Fonctionnalités Clés

1.  **BioHashing (Visage)** : Transformation irréversible et révocable des vecteurs du visage (dlib).
2.  **Fuzzy Vault (Empreinte)** : Cryptosystème polynômial pour verrouiller des secrets avec des empreintes, sans stocker l'image originale.
3.  **Zero Trust Context** : Analyse du contexte (Adresse IP, Heure) pour évaluer la confiance (Trust Score) avant d'autoriser l'accès.
4.  **Multimodal Fusion** : Combinaison pondérée des scores (60% Visage + 40% Empreinte).
5.  **Interface Moderne** : Web App React (Vite) avec design Cybersecurity.

---

## 🛠️ Installation

### Prérequis
*   Python 3.10+
*   Node.js & npm
*   Bibliothèques C++ pour dlib (`sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libx11-dev`)

### 1. Installation Backend
```bash
# Aller dans le dossier
cd Project

# Environnement Virtuel
python3 -m venv venv
source venv/bin/activate

# Dépendances Python
pip install -r requirements.txt
```
*Note : Si les modèles dlib (`.dat`) sont manquants, téléchargez-les depuis http://dlib.net/files/ .*

### 2. Installation Frontend
```bash
cd frontend
npm install
```

---

## 🚦 Démarrage

Il faut lancer le Backend et le Frontend dans deux terminaux séparés.

### Terminal 1 : Backend (API)
```bash
source venv/bin/activate
fuser -k 8000/tcp # Tuer les processus précédents si nécessaire
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*L'API sera disponible sur http://127.0.0.1:8000/docs*

### Terminal 2 : Frontend (Web App)
```bash
cd frontend
npm run dev -- --host
```
*L'application sera accessible sur http://localhost:5173 (ou 5174)*

---

## 🧪 Utilisation

### 1. Enrôlement (`/enroll`)
1.  Entrez un nom d'utilisateur unique.
2.  Capturez votre visage via la Webcam.
3.  (Optionnel) Uploadez une image d'empreinte (utilisez `finger_a.png` généré par le script de test).
4.  Cliquez sur **ENROLL USER**.

### 2. Vérification (`/verify`)
1.  Entrez votre nom d'utilisateur.
2.  Capturez votre visage.
3.  (Optionnel) Uploadez l'empreinte.
4.  Cliquez sur **AUTHENTICATE**.
5.  Le système affichera :
    *   **ACCESS GRANTED** 🟢 (Si biométrie + contexte valides).
    *   **ACCESS DENIED** 🔴 (Si biométrie échoue ou contexte suspect).

---

## 📂 Architecture Technique

### Backend (`/backend`)
*   **FastAPI** : Serveur REST.
*   **SQLAlchemy/SQLite** : Base de données des templates chiffrés.
*   `services/biometric.py` : Logique BioHashing (dlib).
*   `services/fuzzy_vault.py` : Logique Fuzzy Vault (Reed-Solomon / Lagrange).
*   `services/context.py` : Moteur de confiance Zero Trust.

### Frontend (`/frontend`)
*   **React + Vite** : Framework UI.
*   **Vanila CSS** : Styling personnalisé (Thème Dark/Neon).
*   `api.js` : Connecteur vers le Backend.

---

## 🔒 Sécurité & Confidentialité
*   **Aucune donnée brute stockée** : Les images sont détruites après traitement. Seuls les BioHashes et Vaults sont conservés.
*   **Révocabilité** : En cas de vol, on change le Token (Seed) ou le Polynôme, rendant l'ancien template inutile.
*   **Défense en Profondeur** : Même avec les bons biométriques, une IP inconnue ou une heure suspecte peut bloquer l'accès.

---

## 📝 Auteurs
Projet réalisé dans le cadre du module Biometric Security (S5).
