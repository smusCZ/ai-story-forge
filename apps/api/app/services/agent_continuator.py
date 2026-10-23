"""
Agent Continuator – Fáze 6
Autonomní agent, který na základě feedbacku a engagementu rozhoduje o dalším postupu příběhu.

Hard rules:
- Vždy pracuje jen s Character Anchors dané série
- Vždy respektuje GenreProfile
- Preferuje organické pokračování
"""
from uuid import UUID
from typing import Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.story import Story
from app.models.chapter import Chapter
from app.models.character_anchor import CharacterAnchor
from app.models.agent_run import AgentRun
from app.services.feedback_service import compute_chapter_summary, update_story_engagement
from app.services.story_generator import generate_chapter
from app.services.llm import llm_client


Decision = Literal["continue", "rewrite", "branch", "new_arc", "review"]


async def _get_latest_chapter(db: AsyncSession, story_id: UUID) -> Chapter | None:
    result = await db.execute(
        select(Chapter)
        .where(Chapter.story_id == story_id)
        .order_by(Chapter.chapter_number.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _load_context(db: AsyncSession, story_id: UUID) -> dict:
    story = (await db.execute(select(Story).where(Story.id == story_id))).scalar_one_or_none()
    if not story:
        raise ValueError("Story not found")

    chars = (await db.execute(
        select(CharacterAnchor).where(CharacterAnchor.series_id == story.series_id)
    )).scalars().all()

    latest = await _get_latest_chapter(db, story_id)
    feedback_summary = None
    if latest:
        feedback_summary = await compute_chapter_summary(db, latest.id)

    engagement = await update_story_engagement(db, story_id)

    return {
        "story": story,
        "characters": chars,
        "latest_chapter": latest,
        "feedback_summary": feedback_summary,
        "engagement_score": engagement,
    }


async def _decide(context: dict) -> tuple[Decision, str]:
    engagement = context["engagement_score"]
    fb = context["feedback_summary"]
    latest = context["latest_chapter"]

    if not latest:
        return "continue", "Žádná kapitola ještě neexistuje → generuji první."

    likes = fb.likes if fb else 0
    dislikes = fb.dislikes if fb else 0
    comments = fb.recent_comments if fb else []

    if engagement >= 0.65 and likes >= dislikes:
        return "continue", f"Vysoký engagement ({engagement}). Pokračuji v přímé linii."

    if engagement < 0.35 or (dislikes > likes and dislikes >= 2):
        return "rewrite", f"Nízký engagement ({engagement}) nebo převaha dislike. Navrhuji úpravu poslední kapitoly."

    if 0.35 <= engagement < 0.55:
        return "continue", f"Střední engagement ({engagement}). Pokračuji opatrně a sleduji reakce."

    prompt = f"""
Jsi Agent Continuator. Na základě dat rozhodni JEDNU akci.

Engagement score: {engagement}
Likes: {likes}, Dislikes: {dislikes}
Nedávné komentáře: {comments[:3] if comments else "žádné"}
Poslední kapitola: {latest.title} (č. {latest.chapter_number})

Možné akce:
- continue
- rewrite
- branch
- new_arc
- review

Odpověz přesně ve formátu:
DECISION: <akce>
REASON: <krátké zdůvodnění>
"""
    try:
        raw = await llm_client.generate(
            "Jsi rozhodovací agent pro pokračování příběhů. Odpovídej stručně a přesně.",
            prompt,
            temperature=0.3,
            max_tokens=200,
        )
        decision = "continue"
        reason = raw
        for line in raw.splitlines():
            if line.startswith("DECISION:"):
                d = line.replace("DECISION:", "").strip().lower()
                if d in ("continue", "rewrite", "branch", "new_arc", "review"):
                    decision = d
            if line.startswith("REASON:"):
                reason = line.replace("REASON:", "").strip()
        return decision, reason  # type: ignore
    except Exception:
        return "continue", "Fallback: pokračuji (LLM rozhodování selhalo)."


async def run_agent(db: AsyncSession, story_id: UUID, force_action: Decision | None = None) -> dict:
    context = await _load_context(db, story_id)

    if force_action:
        decision = force_action
        reasoning = f"Manuálně vynucená akce: {force_action}"
    else:
        decision, reasoning = await _decide(context)

    output: dict = {
        "decision": decision,
        "reasoning": reasoning,
        "engagement_score": context["engagement_score"],
        "new_chapter_id": None,
    }

    if decision == "continue":
        chapter = await generate_chapter(db, story_id, user_instruction=None, use_inspiration=True)
        output["new_chapter_id"] = str(chapter.id)
        output["chapter_number"] = chapter.chapter_number
        output["chapter_title"] = chapter.title

    elif decision == "rewrite":
        latest = context["latest_chapter"]
        if latest:
            instruction = (
                f"Přepiš/uprav předchozí kapitolu (č. {latest.chapter_number}) tak, "
                f"aby lépe reagovala na feedback publika. Engagement byl nízký. "
                f"Zachovej Character Anchors a žánr."
            )
            chapter = await generate_chapter(db, story_id, user_instruction=instruction, use_inspiration=True)
            output["new_chapter_id"] = str(chapter.id)
            output["chapter_number"] = chapter.chapter_number
            output["note"] = "Vygenerována upravená verze (rewrite flow)"
        else:
            chapter = await generate_chapter(db, story_id)
            output["new_chapter_id"] = str(chapter.id)

    elif decision == "review":
        output["note"] = "Agent požaduje lidskou kontrolu. Generování pozastaveno."

    elif decision in ("branch", "new_arc"):
        instruction = (
            "Vytvoř nové pokračování, které otevírá novou větev / nový arc. "
            "Zachovej Character Anchors a žánr, ale posuň příběh výrazněji."
        )
        chapter = await generate_chapter(db, story_id, user_instruction=instruction, use_inspiration=True)
        output["new_chapter_id"] = str(chapter.id)
        output["chapter_number"] = chapter.chapter_number
        output["note"] = f"Akce {decision} – vygenerováno nové pokračování"

    run = AgentRun(
        story_id=story_id,
        action_taken=decision,
        reasoning=reasoning,
        input_state={
            "engagement_score": context["engagement_score"],
            "latest_chapter_id": str(context["latest_chapter"].id) if context["latest_chapter"] else None,
            "characters_count": len(context["characters"]),
        },
        output=output,
    )
    db.add(run)
    await db.flush()

    return {
        "run_id": str(run.id),
        "story_id": str(story_id),
        "action": decision,
        "reasoning": reasoning,
        "result": output,
    }
