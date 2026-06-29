# LLA Detector
**Application de Vision par Ordinateur pour la Détection du Cancer du Sang**  
ENSPY — Filière AIA4 — Génie Logiciel — Semestre 2

> **Prototype académique.** Ce projet ne constitue pas un dispositif médical certifié. Consultez un professionnel de santé qualifié pour tout diagnostic.

---

## Architecture du projet

```
lla_detector/
│
├── app.py                            ← Point d'entrée — lance le serveur Flask
├── requirements.txt                  ← Dépendances Python
│
├── controllers/
│   └── routes.py                     ← Toutes les routes HTTP (MVC Contrôleur)
│
├── services/
│   ├── preprocessing/
│   │   └── preprocessing_service.py  ← Redimensionnement, normalisation, CLAHE
│   ├── classification/
│   │   ├── classification_service.py ← Chargement modèle + inférence
│   │   └── classification_result.py  ← Objet-valeur résultat
│   ├── explicabilite/
│   │   └── grad_cam_service.py       ← Génération carte Grad-CAM
│   └── export/
│       └── export_service.py         ← Rapport HTML de synthèse
│
├── model/
│   └── model.h5                      ← Poids du modèle entraîné (à placer)
│
├── presentation/
│   ├── templates/
│   │   └── index.html                ← Template HTML principal (Jinja2)
│   └── static/
│       ├── css/main.css              ← Styles
│       └── js/main.js                ← Logique d'interface
│
└── tests/                            ← Tests unitaires 
```

---

## Installation

### Prérequis
- Python 3.10+ (recommandé via Anaconda)
- Git

### 1. Cloner le dépôt
```bash
git clone https://github.com/cskef/lla_detector.git
cd lla_detector
```

### 2. Créer l'environnement virtuel
```bash
conda create -n lla_env python=3.10
conda activate lla_env
python -m venv nom-environnement
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Placer le modèle entraîné
Copier le fichier de poids (`model.h5` ou `model.pt`) dans le dossier `model/` :
```bash
cp model/model.h5
```
> Sans le fichier de poids, l'application démarre en **mode STUB** et retourne des résultats simulés. Cela permet de développer et tester l'interface avant d'avoir le modèle entraîné.

### 5. Lancer l'application
```bash
python app.py
```
Ouvrir le navigateur à l'adresse : **http://127.0.0.1:5000**

---

## Routes HTTP

| Route     | Méthode | Description |
|-----------|---------|-------------|
| `/`       | GET     | Page d'accueil |
| `/upload` | POST    | Validation et aperçu de l'image |
| `/analyze`| POST    | Pipeline complet : prétraitement + inférence + Grad-CAM |
| `/export` | GET     | Rapport HTML téléchargeable |
| `/batch`  | POST    | Analyse par lot d'images |

---

## Modèle IA

Le modèle utilise le **transfert d'apprentissage** :
- Architecture : **DenseNet121** ou **MobileNetV2** (pré-entraîné sur ImageNet)
- Réentraîné sur **ALL-IDB2** (Acute Lymphoblastic Leukemia Image Database)
- Classification binaire : `0` = Cellule saine · `1` = Blaste leucémique
- Entraînement recommandé sur **Google Colab** (GPU requis)

---

## Équipe

- **BILOA ABADJECK Paolo Valéry S.**
- **KENNE KEYANYEM Frank C.**
- **GOUFAN A ETONG Armel K.**

Encadrant : **Dr Willy KENGNE KUNGNE**

---

## Licence

MIT License — voir `LICENSE` pour les détails.  
Dataset ALL-IDB : Labati, Piuri & Scotti (2011) — IEEE ICIP.
