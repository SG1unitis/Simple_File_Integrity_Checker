# Démonstration SIFIC

Cette démonstration montre comment SIFIC peut créer une baseline d’intégrité pour un dossier, puis détecter des modifications.

Le scénario est volontairement simple :

- `demo-clean/` représente un état initial sain ;
- `demo-modified/` représente un état modifié ;
- SIFIC doit détecter :
  - un fichier modifié ;
  - un fichier ajouté ;
  - un fichier supprimé.

---

## 1. Créer une baseline depuis l’état sain

Depuis la racine du projet :

```bash
sific baseline create examples/demo-clean --output examples/baseline.json
```

Sortie attendue :

Baseline créée : examples/baseline.json
Fichiers indexés : 2
Algorithme : sha256

La baseline contient les empreintes des fichiers présents dans examples/demo-clean.

2. Vérifier l’état sain
```bash
sific baseline check examples/demo-clean --baseline examples/baseline.json
```

Sortie attendue :

UNCHANGED: 2
MODIFIED:  0
ADDED:     0
DELETED:   0

Aucun changement n’est détecté.

3. Vérifier un dossier modifié
```bash
sific baseline check examples/demo-modified --baseline examples/baseline.json
```

Sortie attendue :

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

SIFIC détecte correctement :

Type	Fichier	Explication
Modified	app.conf	Le contenu du fichier a changé
Added	suspicious.conf	Le fichier n’existait pas dans la baseline
Deleted	users.conf	Le fichier était présent dans la baseline mais absent du dossier vérifié

4. Exemple en sortie JSON
```bash
sific baseline check examples/demo-modified --baseline examples/baseline.json --json
```

Exemple de sortie :

{
  "added": [
    "suspicious.conf"
  ],
  "baseline": "examples/baseline.json",
  "deleted": [
    "users.conf"
  ],
  "directory": "examples/demo-modified",
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

La sortie JSON permet d’exploiter SIFIC dans des scripts, des contrôles automatisés ou des pipelines CI/CD.

5. Nettoyer la baseline générée

Si besoin :
```bash
rm examples/baseline.json
```

Sous Windows :
```bash
del examples\baseline.json
```
