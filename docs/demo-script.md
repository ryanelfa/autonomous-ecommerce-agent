# Demo script

A 2-minute Loom, plus an opening line for the live interview.

## Opening line (oral)

> « Plutôt que de vous parler d'agents, je vais casser ma prod devant vous et laisser
> mon agent réparer. »

## Loom — 2 minutes

**0:00–0:15 — The living dashboard.**
Open on the running dashboard, incidents already flowing.
> « Voici Belleza Ops, un agent IA autonome qui gère les incidents e-commerce d'une
> marque beauté pendant un pic de ventes. Tout ce que vous voyez tourne en temps réel. »

**0:15–0:50 — The agent resolves (out of stock).**
Click **Rupture de stock**. Narrate the trace as it streams:
> « Il récupère la commande, vérifie le profil de la cliente, contrôle le stock — il est
> à zéro — cherche une alternative dans la même catégorie, la propose, et rédige le
> message à la cliente. Le compteur de CA sauvé monte. »

**0:50–1:20 — The agent knows when to stop (VIP).**
Click **VIP mécontente**.
> « Ici, l'agent enquête… puis s'arrête. Cliente VIP : il escalade en urgent avec un
> résumé pour le conseiller humain, au lieu de bricoler une réponse. Un bon agent, c'est
> aussi savoir ne pas agir. »

**1:20–1:45 — White-label live.**
Switch the brand selector from **Belleza** to **Sportéa**.
> « Même agent, n'importe quel client en 30 secondes : couleurs, logo, catalogue et même
> le ton des réponses changent, sans recharger la page. »

**1:45–2:00 — The engine.**
Show `system_prompt.md` and `core.py` side by side.
> « Tout le comportement est piloté par ce system prompt et ces règles métier. La boucle
> de l'agent est écrite à la main — React, TypeScript, GraphQL, Python, temps réel,
> exactement la stack du poste. »

## Things to have ready before recording

- Backend and frontend both running; simulation ON.
- A valid `ANTHROPIC_API_KEY` in `.env` (otherwise the agent auto-escalates everything).
- Browser at `http://localhost:5173`, window sized so all three columns are visible.
- Let the simulation run ~30s before recording so KPIs aren't at zero.

## If something goes wrong on stage

- No API key / API down → every incident escalates cleanly to a human. The app does not
  crash; you can narrate this as the built-in safety fallback.
- WebSocket drops → the top bar shows "reconnexion…" and the client reconnects
  automatically.
