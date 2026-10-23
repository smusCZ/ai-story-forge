# Přesný postup vývoje AI Story Forge

Tento dokument popisuje **přesný, postupný a praktický** postup vývoje celého programu tak, aby odpovídal všem požadavkům:

- Ukládání obrázků do složek pro inspiraci
- Nastavení žánru a tónu bez omezení
- Character Anchors jako záchytné body konzistence
- Oddělení postav podle sérií (žádné míchání mezi příběhy)
- Autonomní Agent Continuator pro generování pokračování podle reakcí publika

---

## Fáze 0 – Příprava projektu (1–2 dny)

1. Vytvořit monorepo strukturu:
   ```
   ai-story-forge/
   ├── apps/
   │   ├── web/          # Next.js frontend
   │   └── api/          # FastAPI backend
   ├── packages/
   │   ├── agent/        # Continuator Agent (LangGraph)
   │   ├── db/           # Prisma / SQLAlchemy schéma
   │   └── shared/       # společné typy a utility
   ├── docs/
   └── docker-compose.yml
   ```

2. Nastavit Docker Compose:
   - PostgreSQL + pgvector
   - Redis (fronty + cache)
   - MinIO / local S3 pro obrázky (později Cloudflare R2)

3. Základní CI (GitHub Actions) – lint, testy, typecheck.

---

## Fáze 1 – Character Anchors + Series Isolation (priorita č. 1)

**Cíl:** Postavy jsou vždy vázané na konkrétní sérii a nemohou se míchat mezi různými příběhy.

### 1.1 Datový model
- Tabulka `series` (id, name, description, owner_id)
- Tabulka `character_anchors` s povinným `series_id`
- Tabulka `stories` s povinným `series_id`
- Constraint: postava může být použita pouze ve stories stejné série

### 1.2 UI – záložka Character Anchors
- Seznam sérií
- Uvnitř série: seznam postav
- Formulář postavy:
  - Jméno, role, vzhled, osobnost, backstory
  - Vztahy (jen k postavám stejné série)
  - Consistency rules (co postava nikdy neudělá)
  - Reference images (z složek série)

### 1.3 Ochrana proti míchání
- Při generování kapitoly se načítají **pouze** Character Anchors dané série
- Agent Continuator má hard rule: „Nikdy nepoužívej postavy z jiné série“
- Validace na úrovni API i promptu

---

## Fáze 2 – Genre & Story Profile

1. Při vytváření příběhu povinné pole:
   - Hlavní žánr
   - Sekundární žánry / subžánry
   - Tón
   - Tempo / cílová délka kapitol
   - Styl vyprávění

2. Uložení jako `story_profile` (JSONB) + propojení se sérií.

3. Tento profil se **vždy** vkládá do promptu generování i do rozhodování agenta.

---

## Fáze 3 – Image Inspiration System

1. Složky obrázků mohou být:
   - Globální (uživatelské)
   - Vázané na sérii
   - Vázané na konkrétní příběh

2. Při generování kapitoly:
   - Agent nebo generátor vybere relevantní obrázky podle aktuálního kontextu + žánru
   - Embedding (CLIP / SigLIP) + similarity search

3. Upload flow:
   - Drag & drop → automatické vytvoření složky nebo výběr existující
   - Tagování + propojení s postavami (volitelné)

---

## Fáze 4 – Story Generation Engine + Story Graph

1. Základní generování kapitoly (text-only nejdřív)
2. Story Graph:
   - Uzly: postavy, lokace, plot threads, unresolved hooks
   - Hrany: vztahy a kauzality
3. Každá kapitola aktualizuje Story Graph
4. Při generování se do promptu vkládá:
   - Character Anchors (série)
   - Story Profile (žánr + tón)
   - Relevantní část Story Graphu
   - Poslední kapitoly + feedback

---

## Fáze 5 – Feedback Loop

1. Sběr reakcí:
   - Like / Dislike
   - Komentáře
   - Emoji
   - Čas strávený čtením
   - Explicitní „chci tuto větev“

2. Sentiment analysis + engagement score

3. Trigger pro Agent Continuator (automaticky nebo manuálně)

---

## Fáze 6 – Agent Continuator (jádro autonomního chování)

### 6.1 Stav agenta
- story_id, series_id
- character_anchors (pouze dané série)
- story_profile
- story_graph summary
- recent_feedback + engagement_score
- decision + reasoning

### 6.2 Tools
- get_character_anchors(series_id)
- get_story_state
- analyze_feedback
- search_inspiration_images
- generate_chapter
- propose_rewrite
- update_story_graph
- create_branch
- flag_for_human_review

### 6.3 Rozhodovací smyčka
1. Načti Character Anchors + žánr + feedback
2. Analyzuj engagement
3. Rozhodni: Continue / Soft Rewrite / Hard Branch / New Arc / Human Review
4. Generuj s povinným vložením Character Anchors a žánru
5. Aktualizuj Story Graph a naplánuj další krok

### 6.4 Hard rules agenta
- Nikdy nemíchej postavy z různých sérií
- Vždy respektuj consistency rules postav
- Drž se definovaného žánru a tónu
- Preferuj organické pokračování před náhodnými zvraty

---

## Fáze 7 – MVP spuštění (text-only)

1. Backend: FastAPI + PostgreSQL + jednoduchý LangGraph agent
2. Frontend: základní UI pro
   - Správu sérií a Character Anchors
   - Vytvoření příběhu + nastavení žánru
   - Generování kapitoly
   - Zobrazení feedbacku
3. Manuální spuštění agenta přes API
4. Testování konzistence postav napříč kapitolami

---

## Fáze 8 – Rozšíření po MVP

- Multimodal generování (obrázky → ilustrace kapitol)
- Automatické plánování kapitol (cron / queue)
- Branching + hlasování publika o větvích
- Online learning z engagementu
- Multi-story portfolio management
- Export (EPUB, PDF, webtoon)

---

## Pořadí priorit (doporučené)

1. Character Anchors + Series isolation  
2. Genre / Story Profile  
3. Základní generování kapitoly s vynucenou konzistencí  
4. Feedback sběr + engagement score  
5. Agent Continuator (text-only)  
6. Image folders + embeddings  
7. Plná autonomie + UI polish  

---

## Definice hotovo (Definition of Done) pro každou fázi

- Unit + integrační testy
- Dokumentace aktualizovaná
- Hard rules na míchání postav ověřené testem
- Prompt templates verzované v kódu
- Možnost manuálního override člověkem

---

Tento postup je navržen přesně pro účely tohoto programu a respektuje všechny tvoje požadavky (Character Anchors, oddělení sérií, žánr od začátku, autonomní pokračování podle publika).
