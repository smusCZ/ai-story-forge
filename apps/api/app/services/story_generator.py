"""
Story Generation Engine (Phase 4)
Always injects:
- Character Anchors of the series (hard isolation)
- GenreProfile
- Optional image inspiration
- Previous chapters summary
Prepares hooks for Agent Continuator and future anime/manga frame generation.
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.story import Story
from app.models.character_anchor import CharacterAnchor
from app.models.chapter import Chapter
from app.models.image import Image, ImageFolder
from app.services.llm import llm_client


SYSTEM_PROMPT = """Jsi špičkový autor příběhů pro AI Story Forge.
Pravidla (povinná):
1. Absolutně respektuj Character Anchors – nikdy neměň základní osobnost, vzhled, motivace ani consistency_rules postav.
2. Drž se přesně zadaného žánru a tónu.
3. Piš pouze postavy z dané série – žádné cizí postavy.
4. Na konci kapitoly vždy připrav 1–2 otevřené háčky pro pokračování.
5. Pokud je žánr anime / manga / visual novel, piš vizuálně a scénicky (vhodné pro pozdější generování panelů/snímků).
6. Výstup strukturuj přesně podle požadovaného formátu.
"""


def _format_characters(chars: list) -> str:
    if not chars:
        return "Žádné Character Anchors zatím nejsou definovány."
    parts = []
    for c in chars:
        parts.append(
            f"### {c.name} ({c.role or 'role neuvedena'})\n"
            f"- Vzhled: {c.appearance_text or '—'}\n"
            f"- Osobnost: {c.personality}\n"
            f"- Backstory: {c.backstory or '—'}\n"
            f"- Aktuální stav: {c.current_state or '—'}\n"
            f"- Consistency rules (NIKDY neporuš): {c.consistency_rules}\n"
            f"- Vztahy: {c.relationships}"
        )
    return "\n\n".join(parts)


def _format_genre(genre: dict) -> str:
    return (
        f"Hlavní žánr: {genre.get('main')}\n"
        f"Sekundární: {', '.join(genre.get('secondary') or [])}\n"
        f"Tón: {genre.get('tone')}\n"
        f"Tempo: {genre.get('tempo')}\n"
        f"Styl: {genre.get('style')}\n"
        f"Cílová délka kapitoly: {genre.get('target_chapter_length')}\n"
        f"Poznámky: {genre.get('notes') or '—'}"
    )


async def generate_chapter(
    db: AsyncSession,
    story_id: UUID,
    user_instruction: str | None = None,
    use_inspiration: bool = True,
) -> Chapter:
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise ValueError("Story not found")

    chars_result = await db.execute(
        select(CharacterAnchor).where(CharacterAnchor.series_id == story.series_id)
    )
    characters = chars_result.scalars().all()

    prev_result = await db.execute(
        select(Chapter)
        .where(Chapter.story_id == story_id)
        .order_by(Chapter.chapter_number.desc())
        .limit(3)
    )
    prev_chapters = list(reversed(prev_result.scalars().all()))
    prev_summary = "\n\n".join(
        f"Kapitola {c.chapter_number}: {c.title or ''}\n{c.summary or c.content[:400]}"
        for c in prev_chapters
    ) or "Toto je první kapitola."

    next_number = (prev_chapters[-1].chapter_number + 1) if prev_chapters else 1

    inspiration_text = ""
    if use_inspiration:
        img_q = (
            select(Image)
            .join(ImageFolder)
            .where(
                (ImageFolder.series_id == story.series_id) |
                (ImageFolder.story_id == story_id)
            )
            .order_by(Image.created_at.desc())
            .limit(5)
        )
        imgs = (await db.execute(img_q)).scalars().all()
        if imgs:
            inspiration_text = "Vizuální inspirace (popis/tagy):\n" + "\n".join(
                f"- {img.filename or img.url}: tags={img.tags}" for img in imgs
            )

    user_prompt = f"""
## Žánrový profil (povinný)
{_format_genre(story.genre)}

## Character Anchors (série – povinná konzistence)
{_format_characters(characters)}

## Dosavadní děj
{prev_summary}

{inspiration_text}

## Instrukce od uživatele
{user_instruction or "Pokračuj přirozeně v příběhu."}

## Požadovaný výstup (přesně dodrž)
TITLE: <název kapitoly>
SUMMARY: <2–4 věty shrnutí>
CONTENT:
<plný text kapitoly>
HOOKS:
- <háček 1>
- <háček 2>
"""

    raw = await llm_client.generate(SYSTEM_PROMPT, user_prompt, temperature=0.88)

    title = f"Kapitola {next_number}"
    summary = ""
    content = raw
    content_lines = []
    mode = None
    for line in raw.splitlines():
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip() or title
            mode = None
        elif line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
            mode = "summary"
        elif line.startswith("CONTENT:"):
            mode = "content"
        elif line.startswith("HOOKS:"):
            mode = "hooks"
        else:
            if mode == "summary" and line.strip():
                summary += " " + line.strip()
            elif mode == "content":
                content_lines.append(line)

    if content_lines:
        content = "\n".join(content_lines).strip()
    if not summary and content:
        summary = content[:300] + "..."

    chapter = Chapter(
        story_id=story_id,
        chapter_number=next_number,
        title=title,
        content=content,
        summary=summary,
        status="draft",
        generated_by="agent",
        parent_chapter_id=prev_chapters[-1].id if prev_chapters else None,
    )
    db.add(chapter)
    await db.flush()
    await db.refresh(chapter)
    return chapter
