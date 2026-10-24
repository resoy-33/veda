# Contrats — Résumé métier (FR)

> Document destiné à la relecture métier (finance) et au pitch.
> La référence technique complète est `docs/contracts.md`.

## En une phrase

Un dépôt (PDF) devient une **analyse vérifiée et horodatée**, dont chaque chiffre
est traçable jusqu'au document, et dont la preuve est scellée sur Hedera — sans
que personne n'ait besoin de nous faire confiance.

## Le parcours d'un dépôt

1. **Dépôt** — l'émetteur dépose un PDF.
2. **Extraction** — l'agent lit les postes et cite le texte source. Le modèle ne
   calcule **jamais** un chiffre.
3. **Validation** — le code vérifie la cohérence des états et calcule les ratios.
4. **Scellage** — les événements sont inscrits sur Hedera (HCS) ; un certificat
   NFT est émis avec les empreintes (hash).
5. **Vérification** — un tiers reconstitue la preuve à partir du registre public
   (Mirror Node), sans accès à nos serveurs.

## Les 4 événements inscrits sur Hedera

| Événement | Émis par | Contenu |
|---|---|---|
| `filing_submitted` | émetteur | identité de l'émetteur, période, empreinte du PDF |
| `extracted` | agent | empreinte de l'extraction, modèle utilisé, nombre de postes, part vérifiée |
| `validated` | agent | verdict (`pass`/`fail`), liste des contrôles, empreinte des ratios |
| `sealed` | agent | empreinte du rapport + référence du certificat (NFT) |

Chaque message contient l'empreinte du message précédent : la chaîne est
**infalsifiable**. Un dépôt en échec s'arrête à `validated{fail}` — aucun NFT.

## Le certificat (NFT)

- Un **NFT par émetteur et par période** (« Dépôt vérifié »).
- Les métadonnées complètes sont stockées sur Hedera (HFS) ; le NFT pointe vers ce
  fichier.
- Contenu : émetteur, période, secteur, empreintes (PDF, extraction, ratios),
  verdict, identifiant du topic HCS, plage de séquences, modèle, date.

## Référentiel des postes (extraits)

- **Compte de résultat :** chiffre d'affaires, coût des ventes, charges de
  personnel, dotations, résultat d'exploitation, charges d'intérêts, impôt,
  résultat net part du groupe, éléments non récurrents…
- **Bilan — actif :** immobilisations (incorporelles, écarts d'acquisition,
  corporelles, financières), titres mis en équivalence, stocks, clients,
  placements, liquidités, totaux…
- **Bilan — passif :** capitaux propres part du groupe, minoritaires, emprunts,
  fournisseurs, dettes financières courantes, autres passifs, totaux…
- **Flux de trésorerie :** CFO, investissements (Capex), cessions, dividendes
  versés, variation des emprunts…
- **Marché :** cours de clôture, nombre d'actions, dividende par action, effectif.

## Contrôles de cohérence (doivent être ≈ 0)

- `actif_egal_passif` — total actif = total passif.
- `somme_actif` / `somme_passif` — la somme des postes reconstitue le total.
- `ebit_recalcule` / `ebt_recalcule` / `resultat_net_recalcule` — le résultat
  publié correspond aux composantes.
- `coherence_tresorerie` — trésorerie de clôture = liquidités − dettes financières
  courantes.

Tolérance : `max(1 dinar, 0,01 %)`.

## Ratios calculés (familles)

Agrégats · Croissance · Marges · Rentabilité (ROE, ROA, ROCE) · DuPont ·
Liquidité · Efficacité (DIO, DSO, DPO, CCC) · Structure financière et couverture ·
Qualité des résultats · Par action (BPA, DPA, VCPA) · Valorisation (PER, P/B, P/S,
P/FCF, Graham).

Tous les ratios sont **calculés par le code**, à partir des postes validés.

## Rôles

| Rôle | Peut faire |
|---|---|
| Émetteur | déposer un PDF |
| Broker | consulter, vérifier, exporter |
| Vérificateur | vérifier la preuve à partir de la chaîne |
| Admin | reconstruire le cache depuis Hedera |

## Unités

Montants stockés en **dinars** ; affichés en **MTND** (millions) pour coller au
modèle d'analyse.

## Ce que le système garantit — et ne garantit pas

**Garantit :** la provenance (le chiffre vient bien du document), l'attribution
(qui a fait quoi), l'immutabilité (rien ne peut être modifié après coup), et la
vérifiabilité par un tiers.

**Ne garantit pas :** que les comptes de l'émetteur sont « vrais ». Nous certifions
la **traçabilité et l'intégrité de l'analyse**, pas la sincérité des états
financiers.
