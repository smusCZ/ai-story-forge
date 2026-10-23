# AI Story Forge

Komplexní systém pro automatické generování příběhů s vizuální inspirací, Character Anchors a autonomním Agent Continuator.

## Hlavní cíle
- Ukládání uploadnutých obrázků do složek → AI z nich čerpá inspiraci
- Jednoduché nastavení žánru + tónu (bez omezení)
- Character Anchors – pevné záchytné body postav pro konzistenci
- Oddělení postav podle sérií (žádné míchání charakterů mezi příběhy)
- Agent Continuator – autonomně tvoří pokračování a nové příběhy podle reakcí publika

## Dokumentace
- [Přesný postup vývoje](PROCEDURE.md)
- [Architektura systému](docs/ARCHITECTURE.md)
- [Character Anchors + Series isolation](docs/CHARACTER_ANCHORS.md)
- [Agent Continuator specifikace](docs/AGENT_CONTINUATOR.md)
- [Databázové schéma + API](docs/DATABASE_AND_API.md)
- [MVP plán](docs/MVP.md)

## Rychlý start (po implementaci)
1. Vytvoř nový příběh a definuj žánr + tón
2. Přidej Character Anchors a přiřaď je do série
3. Nahraj referenční obrázky do složek
4. Spusť generování první kapitoly
5. Agent Continuator přebírá řízení podle feedbacku publika
