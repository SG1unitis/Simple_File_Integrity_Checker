# SIFIC — Simple File Integrity Checker

**SIFIC** est un outil en ligne de commande écrit en Python pour vérifier l’intégrité de fichiers.

Il permet de :

- générer des empreintes de fichiers ;
- vérifier un fichier à partir d’un hash attendu ;
- créer une baseline d’intégrité pour un dossier ;
- détecter les fichiers modifiés, ajoutés ou supprimés ;
- produire une sortie JSON exploitable dans des scripts ou des pipelines.

SIFIC n’est pas un antivirus, un EDR ou un outil forensic complet. C’est un outil léger de contrôle d’intégrité.

---

## Fonctionnalités

- Génération de hash pour un fichier
- Vérification d’un fichier contre un hash attendu
- Support de SHA-256, SHA-512 et MD5
- Validation stricte du format des hash attendus
- Lecture des fichiers par blocs pour éviter de charger les gros fichiers en mémoire
- Création de baseline d’intégrité pour un dossier
- Comparaison d’un dossier avec une baseline existante
- Détection des fichiers :
  - inchangés ;
  - modifiés ;
  - ajoutés ;
  - supprimés.
- Sortie texte lisible par humain
- Sortie JSON pour automatisation
- Codes retour adaptés à une utilisation en script
- Tests automatisés avec `pytest`
- Intégration continue avec GitHub Actions

---

## Prérequis

- Python 3.9 ou supérieur
- `pip`

Vérifiez la version de Python :

```bash
python --version
```

ou :

```bash
python3 --version
```

---

## Installation

### Installation locale en mode développement

Depuis la racine du projet :

```bash
pip install -e .
```

Après installation, la commande suivante doit être disponible :

```bash
sific --help
```

---

## Utilisation

### Afficher l’aide générale

```bash
sific --help
```

### Afficher l’aide d’une commande

```bash
sific hash --help
sific verify --help
sific baseline --help
sific baseline create --help
sific baseline check --help
```

---

# Commandes principales

## 1. Générer le hash d’un fichier

```bash
sific hash fichier.txt
```

Par défaut, SIFIC utilise SHA-256.

Exemple de sortie :

```text
2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
```

### Choisir un autre algorithme

```bash
sific hash fichier.txt --algo sha512
```

ou :

```bash
sific hash fichier.txt --algo md5
```

MD5 est supporté uniquement pour compatibilité avec d’anciens systèmes. Il ne doit pas être utilisé pour une vérification d’intégrité sensible.

---

## 2. Vérifier un fichier avec un hash attendu

```bash
sific verify fichier.txt --hash <HASH_ATTENDU>
```

Exemple :

```bash
sific verify fichier.txt --hash 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
```

Si le hash correspond :

```text
MATCH
Calculated: 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
```

Si le hash ne correspond pas :

```text
MISMATCH
Calculated: e3b0c44298fc1c149afbf4c8996fb924...
Expected:   2cf24dba5fb0a30e26e83b2ac5b9e29...
```

---

## 3. Créer une baseline d’intégrité

Une baseline est un fichier JSON contenant l’état de référence d’un dossier à un instant donné.

```bash
sific baseline create ./demo --output baseline.json
```

Exemple de sortie :

```text
Baseline créée : baseline.json
Fichiers indexés : 3
Algorithme : sha256
```

La baseline contient notamment :

```json
{
  "algorithm": "sha256",
  "created_at": "2026-05-24T12:00:00Z",
  "files": {
    "app.conf": "hash...",
    "users.conf": "hash..."
  },
  "root": "/chemin/absolu/du/dossier",
  "version": 1
}
```

---

## 4. Vérifier un dossier avec une baseline

```bash
sific baseline check ./demo --baseline baseline.json
```

Exemple sans changement :

```text
UNCHANGED: 2
MODIFIED:  0
ADDED:     0
DELETED:   0
```

Exemple avec changements détectés :

```text
UNCHANGED: 0
MODIFIED:  1
ADDED:     1
DELETED:   1

Modified files:
  - app.conf

Added files:
  - suspicious.conf

Deleted files:
  - users.conf
```

Dans ce cas, SIFIC retourne le code `1`, car l’intégrité n’est plus conforme à la baseline.

---

# Sortie JSON

SIFIC peut produire une sortie JSON lisible par des scripts, des outils d’automatisation ou des pipelines CI/CD.

## Générer un hash en JSON

```bash
sific hash fichier.txt --json
```

Exemple :

```json
{
  "algorithm": "sha256",
  "file": "fichier.txt",
  "hash": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
  "status": "success"
}
```

---

## Vérifier un fichier en JSON

```bash
sific verify fichier.txt --hash <HASH_ATTENDU> --json
```

Exemple en cas de succès :

```json
{
  "algorithm": "sha256",
  "calculated": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
  "expected": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
  "file": "fichier.txt",
  "status": "match"
}
```

Exemple en cas d’échec :

```json
{
  "algorithm": "sha256",
  "calculated": "e3b0c44298fc1c149afbf4c8996fb924...",
  "expected": "2cf24dba5fb0a30e26e83b2ac5b9e29...",
  "file": "fichier.txt",
  "status": "mismatch"
}
```

---

## Créer une baseline en JSON

```bash
sific baseline create ./demo --output baseline.json --json
```

Exemple :

```json
{
  "algorithm": "sha256",
  "baseline": "baseline.json",
  "directory": "./demo",
  "files_indexed": 2,
  "status": "success"
}
```

---

## Vérifier une baseline en JSON

```bash
sific baseline check ./demo --baseline baseline.json --json
```

Exemple sans changement :

```json
{
  "added": [],
  "baseline": "baseline.json",
  "deleted": [],
  "directory": "./demo",
  "modified": [],
  "status": "unchanged",
  "summary": {
    "added": 0,
    "deleted": 0,
    "modified": 0,
    "unchanged": 2
  },
  "unchanged": [
    "app.conf",
    "users.conf"
  ]
}
```

Exemple avec changements :

```json
{
  "added": [
    "suspicious.conf"
  ],
  "baseline": "baseline.json",
  "deleted": [
    "users.conf"
  ],
  "directory": "./demo",
  "modified": [
    "app.conf"
  ],
  "status": "changed",
  "summary": {
    "added": 1,
    "deleted": 1,
    "modified": 1,
    "unchanged": 0
  },
  "unchanged": []
}
```

---

# Codes retour

| Code | Signification |
|---:|---|
| 0 | Succès / intégrité vérifiée |
| 1 | Hash différent / changement détecté |
| 2 | Erreur d’usage CLI générée par `argparse` |
| 3 | Entrée invalide, par exemple hash malformé |
| 4 | Erreur fichier, dossier ou baseline |
| 5 | Erreur interne |

# Exemples rapides

## Exemple complet : baseline

Créer un dossier de démonstration :

```bash
mkdir demo
echo clean > demo/app.conf
echo admin=true > demo/users.conf
```

Créer la baseline :

```bash
sific baseline create demo --output baseline.json
```

Modifier le dossier :

```bash
echo modified > demo/app.conf
echo suspicious > demo/suspicious.conf
rm demo/users.conf
```

Relancer la vérification :

```bash
sific baseline check demo --baseline baseline.json
```

Résultat attendu :

```text
UNCHANGED: 0
MODIFIED:  1
ADDED:     1
DELETED:   1

Modified files:
  - app.conf

Added files:
  - suspicious.conf

Deleted files:
  - users.conf
```

---

# Notes de sécurité

- SHA-256 est l’algorithme utilisé par défaut.
- SHA-512 est également disponible.
- MD5 est considéré comme cassé cryptographiquement.
- MD5 est conservé uniquement pour des besoins de compatibilité.
- SIFIC vérifie l’intégrité de fichiers, mais n’identifie pas la cause d’une modification.
- SIFIC ne détecte pas les malwares.
- SIFIC ne remplace pas un antivirus, un EDR, un SIEM ou un outil forensic.
- Une baseline doit être créée dans un état considéré comme sain.
- Si une baseline est créée après compromission, elle enregistrera un état déjà compromis.


# Tests

Installer les dépendances de test :

```bash
pip install pytest
```

Lancer les tests :

```bash
pytest
```
## Démonstration incluse

Le dossier `examples/` contient une démonstration simple du fonctionnement de SIFIC.

Elle montre comment :

- créer une baseline depuis un dossier sain ;
- vérifier que ce dossier reste inchangé ;
- détecter ensuite un fichier modifié, un fichier ajouté et un fichier supprimé.

Consulter :

```text
examples/demo.md

Commandes principales :

sific baseline create examples/demo-clean --output examples/baseline.json
sific baseline check examples/demo-clean --baseline examples/baseline.json
sific baseline check examples/demo-modified --baseline examples/baseline.json
sific baseline check examples/demo-modified --baseline examples/baseline.json --json
```

Lancez :

```bash
sific baseline create examples/demo-clean --output examples/baseline.json
sific baseline check examples/demo-clean --baseline examples/baseline.json
sific baseline check examples/demo-modified --baseline examples/baseline.json
sific baseline check examples/demo-modified --baseline examples/baseline.json --json
```

Le projet couvre notamment :

- génération de hash SHA-256 ;
- génération de hash SHA-512 ;
- génération de hash MD5 ;
- vérification de hash valide ;
- détection de mismatch ;
- rejet des hash invalides ;
- gestion des fichiers absents ;
- gestion des chemins pointant vers un dossier ;
- création de baseline ;
- chargement de baseline ;
- rejet de baseline invalide ;
- détection de fichiers modifiés ;
- détection de fichiers ajoutés ;
- détection de fichiers supprimés ;
- sortie JSON des commandes CLI.

# Structure du projet

```text
sific/
├── sific/
│   ├── __init__.py
│   ├── baseline.py
│   ├── cli.py
│   ├── hachage.py
│   └── validation.py
├── tests/
│   ├── test_baseline.py
│   ├── test_cli.py
│   ├── test_hachage.py
│   └── test_validation.py
├── .github/
│   └── workflows/
│       └── tests.yml
├── README.md
├── LICENSE.txt
└── pyproject.toml
```

# Licence

Ce projet est distribué sous licence MIT.

# Auteur

Projet développé par **SG1Unitis**.
