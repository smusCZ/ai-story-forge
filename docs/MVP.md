# MVP plán (text-only)

## Cíl MVP
Funkční systém, který:
1. Umožní vytvořit sérii a Character Anchors
2. Vytvoří příběh s definovaným žánrem
3. Vygeneruje kapitolu s vynucenou konzistencí postav
4. Sbírá jednoduchý feedback
5. Spustí Agent Continuator, který rozhodne a vygeneruje pokračování

## Tech stack MVP
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Agent: LangGraph
- Frontend: Next.js (základní formuláře + seznam kapitol)
- LLM: libovolný (OpenAI / Anthropic / Grok / local)

## Minimální implementace agenta
- State s series_id a character_anchors
- Nodes: analyze → decide → generate → save
- Hard filter na series_id při načítání anchors
- Prompt vždy obsahuje Character Anchors + genre

## Kritéria úspěchu MVP
- Postavy se nemíchají mezi sériemi (ověřeno testem)
- Žánr je respektován v generovaných kapitolách
- Agent dokáže na základě negativního feedbacku navrhnout rewrite
- Celý flow jde spustit z UI nebo API
