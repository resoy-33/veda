# Veda — Dépôts financiers vérifiés

Trust layer for financial filings: AI extracts, code validates, Hedera seals.
See `docs/PLAN.md` and `docs/contracts.md`.

## Run

```bash
docker compose up --build
```

- Web: http://localhost:8080
- API health: http://localhost:8000/health

## Interface

- `/login` — connexion et accès démo en un clic (4 rôles).
- `/depots` — registre, indicateurs et périmètre de chaque rôle.
- `/depots/:id` — dossier complet : comptes, ratios, preuve HCS, vérification.
- `/depots/nouveau` — dépôt en trois étapes (soumission, extraction, scellement).
- `/verification` — file de contrôle indépendante pour analystes et auditeurs.
- `/operations` — état du système et reconstruction du cache (administrateur).
- `/compte` — nom affiché, mot de passe, thème clair / sombre / système.

Le thème est mémorisé dans le navigateur. La session JWT est conservée dans
`sessionStorage` et expire après une heure.

## Comptes de démonstration

Mot de passe commun : `demo1234` (comptes de démo, à changer en production).

| email | rôle |
|---|---|
| issuer@lilas.tn | issuer |
| broker@veda.tn | broker |
| verifier@veda.tn | verifier |
| admin@veda.tn | admin |

## Layout

```
api/    FastAPI (backend, Hedera client, ratios)
web/    React (Vite) + nginx
db/     Postgres init scripts (cache, rebuildable from chain)
docs/   plan + contracts
spike/  Day-1 Hedera spike (already passed)
```
