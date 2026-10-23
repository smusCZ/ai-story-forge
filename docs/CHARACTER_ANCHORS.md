# Character Anchors + Series Isolation

## Účel
Character Anchors slouží jako pevné záchytné body pro udržení konzistence a kontinuity postav napříč celým příběhem a všemi automatickými pokračováními.

## Pravidlo oddělení sérií
- Každá postava patří **právě jedné sérii**.
- Příběh patří **právě jedné sérii**.
- Při generování kapitoly se načítají **pouze** Character Anchors dané série.
- Agent Continuator má hard constraint: zakázáno používat postavy z jiné série.

## Datový model (zjednodušeně)

```sql
series (
  id, name, description, owner_id
)

character_anchors (
  id,
  series_id,          -- povinné
  name,
  role,
  appearance_text,
  personality JSONB,
  backstory,
  relationships JSONB, -- pouze ID postav stejné série
  current_state,
  consistency_rules JSONB,
  reference_image_ids UUID[]
)

stories (
  id,
  series_id,          -- povinné
  title,
  genre JSONB,
  ...
)
```

## UI tok
1. Uživatel vytvoří nebo vybere sérii.
2. Uvnitř série spravuje Character Anchors.
3. Při vytváření příběhu vybere sérii → automaticky se načtou všechny její postavy.
4. Možnost „lock“ postavy pro daný příběh (volitelné).

## Validace
- API odmítne pokus přiřadit postavu z jiné série.
- Prompt builder vždy filtruje anchors podle series_id.
- Testy pokrývají pokusy o míchání charakterů.
