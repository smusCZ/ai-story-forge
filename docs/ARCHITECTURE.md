# Architektura AI Story Forge

## Vysokoúrovňový pohled

```
[Frontend – Next.js]
        ↓
[API Gateway – FastAPI]
        ↓
┌─────────────────┬──────────────────────┬─────────────────────┐
│ Image Service   │ Story Generation     │ Feedback & Analytics│
│ (S3 + Embeddings)│ Engine + Story Graph │                     │
└─────────────────┴──────────────────────┴─────────────────────┘
        ↓                    ↓                       ↓
[Vector DB]            [LLM Orchestration]      [PostgreSQL]
        ↓                    ↓
              [Agent Continuator – LangGraph]
                         ↓
               [Story Graph + Versioning]
```

## Klíčové principy

1. **Series Isolation** – postavy a referenční obrázky jsou vždy vázané na sérii.
2. **Character Anchors first** – generování nikdy nezačne bez načtených anchorů.
3. **Genre jako kontrakt** – žánr a tón jsou součástí každého promptu.
4. **Feedback-driven autonomy** – Agent Continuator rozhoduje na základě engagementu.
5. **Human override vždy dostupný**.
