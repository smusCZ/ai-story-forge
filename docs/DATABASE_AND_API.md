# Databázové schéma + API

## Hlavní tabulky

- **series** – izolace postav a příběhů
- **character_anchors** – vázané na series_id
- **stories** – vázané na series_id + genre profile
- **chapters** – s podporou branch_id a parent_chapter_id
- **image_folders** + **images** (s embedding)
- **feedback**
- **agent_runs**
- **story_graph_nodes / edges** (nebo JSONB)

## Klíčové API endpointy

```
POST   /series
GET    /series/{id}/characters
POST   /series/{id}/characters

POST   /stories                    # vyžaduje series_id + genre
GET    /stories/{id}
PATCH  /stories/{id}

POST   /stories/{id}/chapters
GET    /stories/{id}/chapters

POST   /chapters/{id}/feedback
GET    /stories/{id}/feedback/summary

POST   /agent/trigger/{story_id}
GET    /agent/runs/{story_id}

POST   /images/upload
POST   /folders
```

Všechny operace s postavami a generováním jsou filtrovány podle series_id.
