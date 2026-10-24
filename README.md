
<p align="center"><b>Des états financiers vérifiés, prêts avant le marché.</b><br>
Hedera Cross Campus Challenge - ISGT edition</p>

---

## Présentation

**VEDA** transforme un état financier publié (PDF) en une analyse vérifiée et horodatée :

1. **Lire** : dépôt du PDF des états financiers d’une société cotée.
2. **Extraire** : 45 postes extraits, chacun avec sa source dans le document, puis 7 contrôles de cohérence.
3. **Calculer** : ratios d’analyse fondamentale et rapport Excel, calculés par le code (aucun chiffre inventé).
4. **Sceller** : la preuve est inscrite sur **Hedera** ; n’importe qui peut la vérifier sans nous faire confiance.

## Pourquoi Hedera

- **Coût faible et fixe** par transaction
- **Finalité en quelques secondes**
- **Sécurité aBFT** (consensus hashgraph)
- **Preuve horodatée et infalsifiable**

| Service | Rôle dans VEDA |
|---|---|
| **HCS** (Consensus Service) | Journal des 4 événements (dépôt, extraction, validation, scellement), chaînés par empreinte |
| **HTS** (Token Service) | Un certificat NFT par émetteur et par période |
| **HFS** (File Service) | Métadonnées du certificat |
| **Mirror Node** | Vérification indépendante et reconstruction de la base depuis la chaîne |

## Architecture

```
web  (React + nginx)  →  api  (FastAPI)  →  db  (PostgreSQL, cache reconstructible)
                                   └──────→  Hedera testnet (HCS, HTS, HFS, Mirror Node)
```

| Dossier | Contenu |
|---|---|
| `api/` | Backend FastAPI : extraction, validation, ratios, client Hedera |
| `web/` | Interface React (Vite) |
| `db/` | Script d’initialisation PostgreSQL |
| `docs/` | Plan du projet et contrats (schémas HCS / NFT) |
| `scripts/` | Données de démonstration |

## Lancer le projet

**Prérequis :** Docker Desktop et un compte Hedera testnet ([portal.hedera.com](https://portal.hedera.com)).

```bash
# 1. Configurer les variables
cp .env.example .env      # puis renseigner HEDERA_OPERATOR_ID et HEDERA_OPERATOR_KEY

# 2. Démarrer
docker compose up --build
```

- Application : http://localhost:8080
- API (santé) : http://localhost:8000/health

## Comptes de démonstration

| Email | Rôle |
|---|---|
| `analyst@veda.tn` | Analyste |
| `admin@veda.tn` | Administrateur |

Mot de passe : `demo1234` (démo uniquement).

## Équipe

Ahmed Doghmen · Dhouha Ben Rouma · Feriel Bouazizi · Zakaria Ben Salah · Yosr Ferjani
