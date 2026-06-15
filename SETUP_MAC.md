# Installation sur un Mac vierge — pas à pas

Ce guide part d'un Mac **sans rien d'installé**. Compte ~30 minutes la première fois.
Tu vas taper des commandes dans **Terminal** (Cmd + Espace, tape « Terminal », Entrée).

> Astuce : copie-colle chaque commande une par une, et attends qu'elle finisse avant la suivante.

---

## 1. Homebrew (le gestionnaire de paquets de macOS)

Homebrew permet d'installer tout le reste en une ligne chacun.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

À la fin, le script affiche deux commandes « Next steps » à exécuter (elles ajoutent
Homebrew à ton PATH). Sur un Mac Apple Silicon (M1/M2/M3/M4), ce sont en général :

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Vérifie :
```bash
brew --version
```

---

## 2. Les outils : Git, Python, Node, uv

```bash
brew install git python@3.12 node@22 uv
```

Node 22 a parfois besoin d'être « lié » :
```bash
brew link --overwrite node@22
```

Vérifie que tout répond (chaque commande doit afficher un numéro de version) :
```bash
git --version
python3.12 --version
node --version
uv --version
```

---

## 3. (Recommandé) Cursor — l'éditeur de code avec IA

Cursor est l'éditeur idéal pour ce projet : c'est exactement le type d'outil mentionné
dans l'offre AI Builder.

```bash
brew install --cask cursor
```

(Alternative gratuite sans IA intégrée : `brew install --cask visual-studio-code`.)

---

## 4. Récupérer le projet

Tu as deux options.

### Option A — tu as déjà le dossier `agent-war-room` (depuis le zip)

Décompresse le zip, puis dans Terminal :
```bash
cd ~/Downloads/agent-war-room      # adapte le chemin si besoin
```

### Option B — tu le mets sur GitHub (recommandé pour la candidature)

1. Crée un compte sur https://github.com si tu n'en as pas.
2. Crée un dépôt vide nommé `agent-war-room` (sans README).
3. Depuis le dossier du projet :
```bash
cd ~/Downloads/agent-war-room
git init
git add .
git commit -m "Agent War Room — autonomous e-commerce ops agent"
git branch -M main
git remote add origin https://github.com/TON_PSEUDO/agent-war-room.git
git push -u origin main
```
   Le lien `https://github.com/TON_PSEUDO/agent-war-room` est celui que tu mettras dans
   ton mail de candidature.

---

## 5. La clé API Anthropic (pour que l'agent réfléchisse)

1. Va sur https://console.anthropic.com et crée un compte.
2. Ajoute quelques euros de crédit (la démo coûte quelques centimes ; ~5 € suffisent
   largement). Section **Billing**.
3. Crée une clé : **API Keys → Create Key**. Copie-la (elle commence par `sk-ant-...`).
4. Dans le dossier du projet :
```bash
cp .env.example .env
```
5. Ouvre `.env` (dans Cursor, ou `open -e .env`) et colle ta clé :
```
ANTHROPIC_API_KEY=sk-ant-ta-vraie-cle-ici
AGENT_MODEL=claude-sonnet-4-6
```
   Enregistre. **Ne partage jamais cette clé et ne la pousse pas sur GitHub** (le
   fichier `.env` est déjà ignoré par `.gitignore`).

---

## 6. Lancer le backend (Terminal n°1)

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Laisse ce terminal ouvert. Tu dois voir « Application startup complete ».
Test rapide dans un navigateur : http://localhost:8000/health doit afficher `{"ok":true}`.

---

## 7. Lancer le frontend (Terminal n°2)

Ouvre un **nouvel onglet** de Terminal (Cmd + T), puis :
```bash
cd ~/Downloads/agent-war-room/frontend     # adapte le chemin
npm install
npm run dev
```

Ouvre http://localhost:5173 — le dashboard apparaît, la simulation tourne déjà.
Clique sur un bouton en bas (« Rupture de stock », « VIP mécontente »…) pour voir
l'agent travailler en direct.

---

## 8. Pour la vidéo de démo

Installe Loom :
```bash
brew install --cask loom
```
(ou l'extension Chrome sur https://www.loom.com). Suis ensuite `docs/demo-script.md`.

---

## En cas de souci

| Symptôme | Solution |
|---|---|
| `command not found: brew` | Refais l'étape 1 (les deux lignes `eval`), ou ferme/rouvre Terminal. |
| `command not found: uv` | `brew install uv`, puis rouvre Terminal. |
| L'agent escalade TOUT en « urgent » | Ta clé API est absente ou invalide : revérifie `.env` (étape 5). |
| Le dashboard reste sur « Connexion à la War Room… » | Le backend n'est pas lancé : vérifie le Terminal n°1 (étape 6). |
| Port 8000 déjà utilisé | Change le port : `--port 8001`, et adapte l'URL dans `frontend/src/apollo.ts` et `frontend/src/ws.ts`. |
| `npm: command not found` | `brew install node@22` puis `brew link --overwrite node@22`. |

---

## Ordre de redémarrage (les fois suivantes)

Tout est déjà installé, il suffit de :
```bash
# Terminal 1
cd ~/Downloads/agent-war-room/backend && uv run uvicorn app.main:app --reload --port 8000
# Terminal 2
cd ~/Downloads/agent-war-room/frontend && npm run dev
```
