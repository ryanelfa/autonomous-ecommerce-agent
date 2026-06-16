# Agent War Room , Belleza Ops

> Un agent IA autonome qui absorbe les incidents e-commerce pendant un pic de ventes, enquête avec ses outils métier, agit quand il peut préserver la vente, et escalade à un humain quand le cas devient sensible.
>
> Démo portfolio orientée **AI Builder / Agentforce** : React, TypeScript, GraphQL, Python/FastAPI, WebSocket, POO, prompt engineering et tool calling.

---

## La problématique

Imaginez le jour du Black Friday pour une marque de cosmétiques : les commandes explosent, et avec elles les incidents, ruptures de stock, paiements échoués, retards de livraison, demandes de retour, clientes VIP mécontentes.

Dans ce contexte, le problème n'est pas seulement de répondre aux clients. Le vrai enjeu est opérationnel :

- le volume d'incidents dépasse rapidement la capacité humaine ;
- chaque minute de retard peut coûter du chiffre d'affaires et dégrader la satisfaction client ;
- les équipes support doivent distinguer les cas simples, qui peuvent être traités automatiquement, des cas sensibles, qui méritent une intervention humaine.

**Belleza Ops** répond à cette problématique avec un agent IA autonome capable d'absorber le flux, de traiter les incidents prioritaires, et de n'escalader que les situations qui le justifient vraiment.

---

## Le pitch

Pendant un pic de ventes, **Belleza Ops** reçoit des incidents e-commerce en temps réel et les traite comme le ferait une équipe ops augmentée par l'IA.

L'agent peut :

- **détecter** un incident dès son arrivée ;
- **enquêter** avec ses outils : commande, client, stock, base de connaissances ;
- **agir** : proposer un produit de substitution, rembourser, appliquer un geste commercial ;
- **préserver du chiffre d'affaires** lorsqu'une substitution ou un geste permet d'éviter une perte de vente ;
- **s'arrêter au bon moment** : les cas sensibles, comme une cliente VIP mécontente, sont escaladés à un humain avec un résumé exploitable.

L'objectif n'est pas de faire un chatbot qui répond à tout. L'objectif est de montrer un agent métier capable de décider quand agir, quand ne pas agir, et comment garder l'humain dans la boucle.

---

## Démo recommandée

La démo a été pensée comme une séquence courte, visuelle et orientée valeur business.

### 1. L'agent résout une rupture de stock

Injection manuelle d'une **rupture de stock**.

L'agent :

1. récupère la commande ;
2. vérifie le profil client ;
3. contrôle le stock du produit ;
4. cherche une alternative dans la même catégorie ;
5. propose un produit de substitution ;
6. rédige une réponse client ;
7. met à jour le chiffre d'affaires estimé préservé.

C'est le scénario principal : il montre que l'agent ne génère pas seulement du texte, mais appelle des outils et prend une action métier.

### 2. L'agent sait s'arrêter sur une VIP mécontente

Injection d'une **cliente VIP mécontente**.

L'agent collecte le contexte puis escalade le dossier à un conseiller humain en priorité urgente.

C'est volontaire : un bon agent n'est pas un agent qui automatise tout. C'est un agent qui sait reconnaître les limites de l'automatisation.

### 3. Le white-label

Passage de **Belleza** à **Sportéa** depuis la barre supérieure.

Les couleurs, le logo, le catalogue et le ton des réponses changent sans rechargement de page. Le moteur agent reste le même : seule la configuration de marque change.

---

## Architecture

```text
┌─────────────┐   WebSocket : trace live, KPIs   ┌──────────────────────┐
│   Frontend  │ <─────────────────────────────── │       Backend        │
│ React + TS  │                                  │      FastAPI         │
│ Apollo      │   GraphQL : bootstrap, actions   │                      │
│ Tailwind    │ ───────────────────────────────> │  ┌────────────────┐  │
└─────────────┘                                  │  │  Simulateur    │  │
                                                 │  │  asyncio       │  │
                                                 │  └───────┬────────┘  │
                                                 │          │ incident  │
                                                 │          v           │
                                                 │  ┌────────────────┐  │
                                                 │  │  Boucle agent  │  │
                                                 │  │  écrite main   │  │
                                                 │  │  Anthropic API │  │
                                                 │  └───────┬────────┘  │
                                                 │          │ outils    │
                                                 │          v           │
                                                 │  ┌────────────────┐  │
                                                 │  │ 8 outils POO   │  │
                                                 │  │ SQLite/SQLModel│  │
                                                 │  │ Base de règles │  │
                                                 │  └────────────────┘  │
                                                 └──────────────────────┘
```

L'application est volontairement simple à lancer : pas de base distante, pas de broker, pas de Docker obligatoire. L'état est stocké localement dans SQLite.

---

## Comment l'agent raisonne

L'agent reçoit un incident avec un contexte minimal : type d'incident, message client, commande associée.

Il doit ensuite **enquêter avant d'agir** :

1. récupérer la commande ;
2. récupérer le profil client ;
3. consulter le stock ou la base de connaissances ;
4. choisir une seule action terminale ;
5. envoyer une réponse client ou créer une escalade humaine.

Chaque étape est diffusée en temps réel dans le dashboard via WebSocket : raisonnements, appels d'outils, résultats d'outils, réponse client, résolution et mise à jour des KPIs.

Le comportement est piloté par :

- un **system prompt** : `backend/app/agent/prompts/system_prompt.md` ;
- des **règles métier** ;
- une **boucle agent écrite à la main** dans `backend/app/agent/core.py`.

Aucun framework d'agent type LangChain n'est utilisé. La boucle suit directement le protocole de tool calling du modèle.

---

## Les règles métier principales

Quelques exemples de règles encodées dans le comportement de l'agent :

- une **plainte VIP** est toujours escaladée à un humain en priorité urgente ;
- une **rupture de stock** doit d'abord chercher un produit de substitution dans la même catégorie, avec un prix proche ;
- si aucune alternative n'existe, l'agent peut rembourser dans la limite autorisée ;
- les remboursements sont plafonnés à 200 € ;
- les bons d'achat sont plafonnés à 30 € ;
- en cas d'erreur LLM ou d'échec d'outil, le serveur ne tombe pas : l'incident est escaladé proprement.

---

## Les 8 outils de l'agent

| Outil | Rôle | Action terminale |
|---|---|---|
| `get_order` | Récupère la commande et le produit associé | Non |
| `get_customer` | Récupère le profil client, son statut et sa valeur vie client | Non |
| `check_stock` | Vérifie le stock et cherche des alternatives valides | Non |
| `search_kb` | Interroge une mini base de connaissances métier | Non |
| `refund_order` | Rembourse une commande dans la limite autorisée | Oui |
| `propose_substitute` | Remplace le produit par une alternative compatible | Oui |
| `apply_voucher` | Applique un geste commercial plafonné | Oui |
| `escalate_to_human` | Crée un ticket pour un conseiller humain | Oui |

---

## Chiffre d'affaires estimé préservé

Le compteur principal affiche une estimation prudente du chiffre d'affaires préservé.

| Issue | Calcul |
|---|---:|
| Substitution | 100 % du montant de la commande |
| Bon d'achat | 50 % du montant de la commande |
| Réponse informative | 30 % du montant de la commande |
| Remboursement | 0 € |
| Escalade humaine | 0 € |

Cette métrique n'est pas présentée comme un gain exact. C'est un indicateur explicable qui permet de comparer les issues : préserver une vente, récupérer une vente probable, informer sans rembourser, ou résoudre à coût nul pour le client mais sans chiffre d'affaires préservé.

---

## White-label en 30 secondes

L'application peut changer de marque sans redéploiement.

La configuration de marque est pilotée par `backend/brands.json` :

- nom ;
- logo SVG généré ;
- palette de couleurs ;
- catalogue produit ;
- ton des réponses.

Le même moteur agent peut ainsi passer de **Belleza**, marque cosmétique, à **Sportéa**, marque sport, sans recharger la page.

Toutes les marques, clientes et produits sont fictifs. Aucun asset propriétaire n'est utilisé.

---

## Lancer le projet localement

### Prérequis

- Python 3.12 ou plus ;
- Node.js 20 ou plus ;
- `uv` ;
- une clé API Anthropic.

### 1. Configurer la clé API

```bash
cp .env.example .env
```

Puis modifier `.env` :

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Ne jamais publier ce fichier. Il doit rester ignoré par Git.

### 2. Lancer le backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --port 8000
```

Le backend écoute sur :

```text
http://127.0.0.1:8000
```

### 3. Lancer le frontend

Dans un deuxième terminal :

```bash
cd frontend
npm install
npm run dev
```

Puis ouvrir :

```text
http://localhost:5173
```

---

## Réinitialiser la démo

Pour remettre à zéro les incidents, les commandes, les tickets, les stocks et le chiffre d'affaires estimé préservé, supprimer la base SQLite locale.

Depuis le dossier `backend` :

```bash
rm -f warroom.db
```

Puis relancer le backend :

```bash
uv run uvicorn app.main:app --port 8000
```

Une nouvelle base sera créée automatiquement au démarrage.

---

## Démonstration sans gaspiller de crédits API

Pour tester l'interface sans consommer inutilement l'API :

1. lancer backend et frontend ;
2. mettre la simulation sur pause ;
3. injecter un seul incident à la fois ;
4. attendre la fin complète de l'agent ;
5. arrêter le backend après la démonstration.

Séquence conseillée pour une vidéo courte :

```text
1. Rupture de stock → substitution → CA estimé préservé
2. VIP mécontente → escalade humaine
3. Belleza → Sportéa → white-label
4. Ouverture rapide de system_prompt.md et core.py
```

---

## Choix de conception

- **Pas de framework d'agent** : la boucle est volontairement écrite à la main pour maîtriser chaque étape.
- **Tool calling explicite** : l'agent ne devine pas, il appelle des outils métier.
- **Humain dans la boucle** : les cas sensibles sont escaladés au lieu d'être automatisés à tout prix.
- **Temps réel via WebSocket** : la trace agent est diffusée en direct au frontend.
- **GraphQL pour l'état initial et les mutations** : incidents, KPIs, marque active, simulation.
- **SQLite local** : simplicité de lancement, aucun service externe hors API LLM.
- **Fallback de sécurité** : une erreur LLM ou outil ne fait jamais tomber le serveur ; elle déclenche une escalade.
- **Messages clients simulés par templates** : le LLM est réservé au raisonnement agent, ce qui limite coût et latence.

---

## Stack technique

### Backend

- Python 3.12
- FastAPI
- Strawberry GraphQL
- SQLModel
- SQLite
- Anthropic SDK
- asyncio
- Programmation orientée objet

### Frontend

- Vite
- React 18
- TypeScript strict
- Apollo Client
- Tailwind CSS
- WebSocket

---

## Pourquoi ce projet

Ce projet a été construit comme une démonstration concrète de compétences attendues pour un rôle **AI Builder / Agentforce** :

- concevoir le raisonnement d'un agent ;
- définir des règles métier dans un prompt système ;
- exposer des outils déterministes au modèle ;
- évaluer les sorties de l'IA avec des métriques explicables ;
- construire une interface temps réel ;
- garder l'humain dans la boucle ;
- transformer un problème business en solution agentique.

L'enjeu n'est pas seulement de montrer une application qui fonctionne. L'enjeu est de montrer une façon de penser : partir d'un problème opérationnel réel, concevoir un agent encadré, le brancher à des outils métier, mesurer son impact, et savoir quand il doit passer la main.
