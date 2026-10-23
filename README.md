# AI Story Forge

Komplexní systém pro automatické generování příběhů s vizuální inspirací, Character Anchors a autonomním **Agent Continuator**.

## Hlavní vlastnosti

- **Character Anchors** – pevné záchytné body postav (izolované podle sérií)
- **Genre Profile** – povinné nastavení žánru a tónu od začátku
- **Image Inspiration** – složky obrázků vázané na sérii/příběh
- **Story Generation** – generování kapitol s vynucenou konzistencí
- **Feedback Loop** – like/dislike/comment/time_spent → engagement score
- **Agent Continuator** – autonomně rozhoduje a generuje pokračování

## Rychlý start

```bash
# 1. Naklonuj repo
git clone https://github.com/smusCZ/ai-story-forge.git
cd ai-story-forge

# 2. Bootstrap (Docker + DB + deps)
cp .env.example .env
# uprav .env (hlavně LLM_API_KEY nebo nastav Ollama)
./scripts/bootstrap.sh

# 3. Spusť API
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: **http://localhost:8000/docs**

## Typický flow

1. `POST /api/v1/series` → vytvoř sérii
2. `POST /api/v1/series/{id}/characters` → přidej Character Anchors
3. `POST /api/v1/stories` → vytvoř příběh (povinný genre + series_id)
4. `POST /api/v1/images/folders` + upload → inspirace
5. `POST /api/v1/stories/{id}/chapters/generate` → první kapitola
6. Publikum dává feedback → `POST /api/v1/chapters/{id}/feedback`
7. `POST /api/v1/agent/trigger/{story_id}` → Agent Continuator rozhodne a pokračuje

## Agent Continuator – akce

| Akce | Význam |
|------|--------|
| continue | Generuje další kapitolu |
| rewrite | Upraví směr podle špatného feedbacku |
| branch / new_arc | Výraznější změna směru |
| review | Požádá o lidskou kontrolu |

## Free / local LLM

V `.env` nastav např.:

```env
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3.3
```

Doporučené free modely 2026: Llama 3.3, Qwen3, DeepSeek-V3, GLM.

## Struktura

```
apps/api/          → FastAPI backend
packages/db/       → SQL schema
scripts/           → bootstrap + init_db
docs/              → specifikace fází
```

## Stav (v0.6.0+)

- [x] Series + Character Anchors (izolace)
- [x] Genre Profile
- [x] Image folders + upload
- [x] Story + Chapter generation
- [x] Feedback + engagement score
- [x] Agent Continuator + /recommend
- [ ] Frontend UI
- [ ] Plné větvení příběhů
- [ ] Automatický scheduling agenta
- [ ] SigLIP2 embeddings
- [ ] Anime/manga panel generation
