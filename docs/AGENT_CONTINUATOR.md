# Agent Continuator – kompletní specifikace

## Role
Autonomní agent, který po zhlédnutí a reakcích publika generuje další kapitoly, provádí úpravy a případně spouští nové příběhy ve stejné sérii.

## State
```json
{
  "story_id": "uuid",
  "series_id": "uuid",
  "story_profile": { "genre": "...", "tone": "...", ... },
  "character_anchors": [ ... ],   // pouze daná série
  "story_graph_summary": "...",
  "recent_feedback": { ... },
  "engagement_score": 0.82,
  "decision": "continue|rewrite|branch|new_arc|review",
  "reasoning": "...",
  "new_chapter": null
}
```

## Tools
1. `get_character_anchors(series_id)`
2. `get_story_state(story_id)`
3. `get_recent_feedback(story_id, limit)`
4. `analyze_feedback_sentiment(feedback)`
5. `search_inspiration_images(series_id, query, limit)`
6. `generate_chapter(prompt_context)`
7. `propose_rewrite(chapter_id, reason)`
8. `update_story_graph(updates)`
9. `create_branch(story_id, name)`
10. `flag_for_human_review(reason)`
11. `schedule_next_run(story_id, delay_hours)`

## Hard Rules (systémový prompt)
- Vždy pracuj pouze s Character Anchors dané série.
- Nikdy neměň základní osobnost, vzhled ani klíčové motivace postav bez záznamu.
- Drž se definovaného žánru a tónu.
- Preferuj organické pokračování.
- Při nízkém engagementu nejdřív analyzuj příčinu.

## Rozhodovací smyčka
1. Načti stav + anchors + feedback
2. Analyzuj engagement
3. Rozhodni akci
4. Generuj (s povinným kontextem)
5. Aktualizuj Story Graph
6. Naplánuj další krok nebo ukonči
