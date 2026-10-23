# AI Story Forge — technický audit a plán stabilizace

- **Projekt:** `smusCZ/ai-story-forge`
- **Základ auditu:** větev `main`, stav souborů načtený při přípravě tohoto dokumentu
- **Verze uvedená aplikací:** `0.6.0`
- **Účel:** zdokumentovat ověřená zjištění z revize zdrojového kódu a navrhnout bezpečné pořadí dalšího vývoje.
- **Důležité omezení:** tento dokument není potvrzením, že aplikace byla spuštěna. Zatím neproběhly lokální testy, integrační testy, sken závislostí ani test nasazení. Každé tvrzení o chování runtime je proto označeno jako neověřené, pokud vyplývá jen ze zdrojového kódu.

## 1. Shrnutí pro rozhodování

Projekt má použitelný základ backendu: FastAPI, SQLAlchemy async, modely pro série/příběhy/kapitoly/obrázky/feedback, službu generování kapitol a Agent Continuator. Doporučení je zachovat tyto funkční části a zpevnit je po malých, testovatelných krocích.

**Pořadí priorit:**

1. P0 — bezpečnost a hranice důvěry: autentizace/autorizace podle zamýšleného provozu, CORS, konfigurace, uploady a chybové odpovědi.
2. P1 — integrita dat: konzistence série/postav/obrázků, transakce, databázové migrace, jednoznačné číslování kapitol.
3. P1 — spolehlivost generování: validovaný výstup modelu, časové limity, idempotence, historie verzí a ochrana proti duplicitním běhům agenta.
4. P1 — testovací základ a CI, aby každá změna byla ověřitelná.
5. P2 — skutečný Story Graph a verzované větve příběhu.
6. P2 — fronta úloh a plánování autonomního agenta.
7. P3 — frontend, embeddings a multimodální/anime/manga výstupy po stabilizaci API.

## 2. Rozsah dosavadního průchodu

Byly prohlédnuty vybrané soubory README, PROCEDURE, Docker Compose, environmentální ukázka, vstup aplikace, nastavení a databázová relace, routery sérií/příběhů/kapitol/feedbacku/agenta/obrázků, služba generování příběhů, služba feedbacku, klient LLM, úložiště obrázků, inicializace DB a seznam závislostí.

Tento výběr není úplný audit všech souborů. Chybí potvrzení všech modelů a schémat, konfigurace CI, testů, migrací, deploymentu a skutečného běhu.

## 3. Zjištění z kódu

### ASF-SEC-001 — Autorizace a izolace dat (P0, podmíněno víceuživatelským provozem)

**Pozorování:** `apps/api/app/routers/series.py` vytváří sérii bez předání vlastníka a endpoint pro výpis sérií dotazuje všechny série. Prohlédnuté endpointy příběhů, feedbacku a obrázků rovněž neukazují společnou autentizační/autoriz­ační závislost.

**Dopad:** pokud má aplikaci používat více účtů nebo bude dostupná na internetu, může hrozit čtení či změna cizích dat. Z tohoto průchodu nelze vyloučit ochranu na proxy nebo v jiné vrstvě; před opravou je nutné zkontrolovat celou aplikaci.

**Návrh:**
- rozhodnout, zda MVP je single-user/local-only, nebo multi-user;
- pro multi-user přidat model uživatele, autentizaci a centrální závislost aktuálního uživatele;
- přidat `owner_id` na kořenové objekty a kontrolovat vlastnictví u každé operace;
- autorizaci uplatnit i při přístupu přes vnořené ID (story, chapter, folder, image, feedback, agent run);
- otestovat, že uživatel A nemůže číst ani měnit objekty uživatele B.

### ASF-SEC-002 — CORS a bezpečná konfigurace (P0 před veřejným nasazením)

**Pozorování:** `apps/api/app/main.py` nastavuje `allow_origins=["*"]` spolu s `allow_credentials=True`. `apps/api/app/core/config.py` má výchozí `debug=True`; SQLAlchemy echo je tímto nastavením také řízeno. `docker-compose.yml` obsahuje pevné výchozí databázové a MinIO přihlašovací údaje a zveřejňuje porty služeb.

**Dopad:** příliš široké hranice důvěry, možnost nechtěného odhalení detailů konfigurace/logů a riziko, pokud se výchozí hodnoty použijí mimo lokální vývoj. FastAPI dokumentace doporučuje při credentials výslovný seznam povolených originů.

**Návrh:**
- oddělit vývojovou a produkční konfiguraci;
- nastavit bezpečné výchozí hodnoty (`DEBUG=false`);
- načítat CORS allowlist z konfigurace a explicitně uvést povolené originy;
- porty DB/Redis/MinIO nevystavovat veřejně, pokud to není potřeba;
- produkční tajemství načítat ze secret manageru nebo prostředí, nikdy je necommitovat;
- přidat startovací validaci, která odmítne nebezpečnou produkční konfiguraci.

### ASF-SEC-003 — Uploady obrázků (P1)

**Pozorování:** `apps/api/app/services/storage.py` nejprve čte celý upload do paměti a až poté kontroluje limit 15 MB. Typ se odvozuje hlavně z přípony. Soubor je vystaven přes statický mount `/uploads`.

**Dopad:** velké requesty mohou spotřebovat zbytečně mnoho paměti; přípona sama neověřuje obsah; veřejné servírování může zpřístupnit všechny uložené soubory bez jemnozrnné autorizace.

**Návrh:**
- zavést limit requestu na proxy/API a streamovat data po blocích s průběžným počítáním bajtů;
- kontrolovat skutečný formát/signaturu a dekódovat obrázek bezpečnou knihovnou;
- povolit jen formáty, které aplikace opravdu potřebuje;
- generovat interní název souboru, zachovat původní název jen jako metadata;
- ukládat mimo veřejný webroot nebo používat autorizované endpointy/podepsané URL;
- přidat limity počtu souborů a celkové kvóty, úklid neúspěšných uploadů a testy mazání DB záznamu versus fyzického souboru.

### ASF-DATA-001 — Integrita vazeb mezi sérií, příběhem a obrázky (P1)

**Pozorování:** tvorba příběhu ověřuje existenci série. Tvorba složky obrázků ověřuje existenci `series_id` a `story_id` samostatně; z prohlédnuté části není patrné ověření, že příběh patří do stejné série jako složka. Generátor načítá postavy podle `story.series_id`, což je správný základ pro izolaci, ale validace vazeb musí být konzistentní v celém API i databázi.

**Návrh:**
- definovat invarianty: příběh patří právě do jedné série; postava patří do jedné série; složka může být globální, sériová nebo příběhová, ale nesmí mít rozporné vazby;
- ověřovat invarianty v aplikační vrstvě a tam, kde je to možné, v databázových omezeních;
- reference na postavy z jiné série musí být odmítnuty při vytvoření i aktualizaci;
- přidat integrační testy pro chybné a hraniční kombinace ID.

### ASF-GEN-001 — Validace výstupu LLM a chybové odpovědi (P1)

**Pozorování:** `story_generator.py` žádá model o textové značky TITLE/SUMMARY/CONTENT/HOOKS a následně výstup parsuje řádek po řádku. `llm.py` volá OpenAI-kompatibilní endpoint a čte `choices[0].message.content`. Routery kapitol a agenta vracejí text výjimky klientovi.

**Dopad:** neočekávaný formát modelu může vytvořit nekvalitní nebo neúplný záznam. Vrácení surové výjimky může odhalit interní detaily poskytovatele či infrastruktury.

**Návrh:**
- oddělit volání modelu, parsování, validaci a ukládání;
- použít Pydantic výstupní schéma (nebo robustní parser s validací) pro název, shrnutí, obsah a háčky;
- při nevalidním výstupu povolit omezený počet opravovacích pokusů;
- nastavit konfigurovatelné timeouty, omezené retry s backoffem, maximální velikost odpovědi a bezpečné logování;
- klientům vracet obecný chybový kód a korelační ID; detaily ponechat v serverových logách bez klíčů a citlivých promptů.

### ASF-AGENT-001 — Semantika rewrite/branch a bezpečnost běhů (P1)

**Pozorování:** `agent_continuator.py` rozhoduje mezi continue/rewrite/branch/new_arc/review. Akce rewrite a branch/new_arc volají stejnou službu pro generování nové kapitoly s instrukcí. Z prohlédnutého kódu tedy nevyplývá skutečné přepsání uložené kapitoly ani vytvoření samostatné větve. Endpoint trigger je synchronní a prohlédnutá část neukazuje ochranu proti souběžným spuštěním.

**Návrh:**
- do zavedení verzování přejmenovat chování na „návrh alternativní kapitoly“ nebo implementovat skutečné verze;
- přidat `chapter_revision` nebo podobný nemazatelný záznam historie;
- větve modelovat samostatně, ne pouze prompt instrukcí;
- přidat idempotency key / zámek na příběh, stav běhu a ochranu proti duplicitnímu triggeru;
- limitovat počet automatických kroků, náklady a opakování; akce s dopadem na schválený děj posílat ke schválení.

### ASF-FEEDBACK-001 — Výpočet engagementu (P1/P2)

**Pozorování:** `feedback_service.py` používá slovníkové hledání sentimentu a skóre engagementu odvozuje z likes/dislikes, komentářů, času a počtu likes. Při žádných reakcích vrací nulu. Zároveň `update_story_engagement` znovu načítá shrnutí všech kapitol.

**Dopad:** skóre je heuristika, nikoli spolehlivý model čtenářského zájmu; část výpočtu může být citlivá na počet kapitol a reakce a při větších datech drahá. Slovníkové hledání může chybně vyhodnocovat kontext, negaci a vícejazyčné komentáře.

**Návrh:**
- zveřejnit definici metriky a její limity;
- ošetřit duplicitní feedback, validovat typy a rozsah času čtení;
- oddělit kvalitu příběhu, míru reakcí a jistotu signálu;
- přidat minimální počet hlasů a „nedostatek dat“ jako samostatný stav;
- nejprve optimalizovat SQL agregace a indexy, až poté přidávat model sentimentu.

### ASF-DB-001 — Migrace databáze (P1)

**Pozorování:** Alembic je uveden v requirements, ale `scripts/init_db.py` používá `Base.metadata.create_all`. To je vhodné pro první vytvoření schématu, nikoli jako jediná strategie pro řízené změny existujících instalací.

**Návrh:**
- zkontrolovat existující migrace a aktuální modely;
- připravit Alembic baseline a následné verzované migrace;
- nikdy automaticky nemazat uživatelská data kvůli změně schématu;
- přidat test migrace z prázdné DB i z předchozí verze.

### ASF-TEST-001 — Testy a CI (P1)

**Pozorování:** v tomto průchodu nebyla potvrzena existence ani pokrytí testů. Neznamená to, že v repozitáři žádné testy nejsou.

**Návrh:** vyhledat veškeré testy a workflow; následně přidat pytest, testovací PostgreSQL, lint, typovou kontrolu, testy API a bezpečnostní regresní scénáře. Každá oprava P0/P1 musí mít reprodukční test.

## 4. Cílová architektura

Zachovat existující vrstvy a vyjasnit jejich odpovědnosti:

- **API (FastAPI):** validace requestů, autentizace, autorizace, HTTP chybové kódy.
- **Application/services:** orchestrace use-case, transakční hranice, agent run lifecycle.
- **Domain:** invarianty sérií, postav, kapitol, větví a stavu světa.
- **Persistence:** SQLAlchemy modely, explicitní indexy/constraints, Alembic migrace.
- **LLM providers:** jednotné rozhraní, timeouty, retry, telemetrie, validované strukturované výstupy.
- **Storage:** rozhraní pro lokální storage a S3/MinIO; přístupové politiky a kvóty.
- **Background jobs:** až po stabilizaci synchronních use-case; Redis je již v Compose, ale přítomnost Redis sama o sobě nedokládá frontu úloh.
- **Frontend:** samostatná aplikace, která volá pouze veřejné API; UI nesmí obcházet autorizaci backendu.

## 5. Navržený datový model pro další fáze

Jde o návrh, nikoli tvrzení, že tyto tabulky už existují.

- `users`: identita a stav účtu, pokud bude multi-user režim.
- `series`: vlastník, metadata a nastavení světa.
- `character_anchors`: série, základní identita, pravidla konzistence, aktuální stav, reference.
- `stories`: série, žánrový profil, stav, aktuální větev.
- `chapters`: obsah aktuální verze, pořadí, stav schválení, shrnutí.
- `chapter_revisions`: neměnné revize textu, autor změny, důvod a timestamp.
- `story_branches`: rodičovská větev, bod rozvětvení, název a stav.
- `story_facts` / `story_events`: potvrzená fakta, události, časová osa, zdroj kapitoly a míra jistoty.
- `plot_threads`: otevřené a uzavřené zápletky, poslední výskyt, stav a plánované návaznosti.
- `agent_runs`: stav, akce, vstupní snapshot, výsledek, chyby, čas, spotřeba a idempotency key.
- `feedback`: kapitola/revize, uživatel nebo anonymní session podle zvoleného režimu, typ, obsah, timestamp.
- `image_folders` / `images`: vlastník, série/příběh, metadata, MIME/formát, velikost, checksum, storage key.
- vektorové embeddings přidat až s definovaným use-case, indexem, licencemi dat a měřitelným přínosem.

## 6. Fázovaný plán implementace

### Fáze A — inventura a reprodukovatelnost

- Získat úplný strom repozitáře a ověřit modely, schémata, migrace, testy, CI a deployment.
- Zprovoznit lokální prostředí podle README.
- Zaznamenat příkazy, verze, chyby a výchozí API smoke testy.
- **Hotovo, když:** existuje reprodukovatelný postup startu a seznam skutečně spuštěných testů.

### Fáze B — P0 bezpečnost

- Rozhodnout single-user vs multi-user.
- Opravit CORS a produkční defaulty.
- Zavést autentizaci/autorizaci nebo explicitně uzamknout lokální režim.
- Zabezpečit uploady a chybové odpovědi.
- **Hotovo, když:** negativní testy pro nepovolený přístup, CORS, přehnanou velikost a falešný formát souboru procházejí.

### Fáze C — integrita databáze a API

- Ověřit všechny vazby série/story/character/image/chapter.
- Přidat constraints a indexy podle skutečných dotazů.
- Zavést Alembic migrace a test rollback/upgrade.
- **Hotovo, když:** neplatné vazby jsou odmítnuty na API i DB úrovni tam, kde je to možné.

### Fáze D — generování a agent

- Validovaný výstup LLM a řízené chyby.
- Transakční ukládání a jednoznačné číslování kapitol.
- Agent run lifecycle, idempotence, timeouty, retry, rozpočet a lidské schválení.
- Revize kapitol a skutečné větve.
- **Hotovo, když:** nevalidní odpověď modelu nepoškodí databázi a opakovaný trigger nevytváří nechtěné duplicity.

### Fáze E — Story Graph a dlouhodobá paměť

- Extrahovat kandidátní fakta a události z kapitoly.
- Odlišit fakta potvrzená autorem od inference modelu.
- Verzovat fakta s odkazem na kapitolu/odstavec a časovou platností.
- Před generováním vyhledat jen relevantní fakta, vztahy a otevřené dějové linky.
- **Hotovo, když:** sada dlouhých regresních příběhů prokáže konzistenci a autor může opravit chybnou paměť.

### Fáze F — frontend a multimodální rozšíření

- UI pro série, postavy, profil žánru, kapitoly, revize, feedback a obrazovou knihovnu.
- Responzivní mobilní/tablet/desktop layout a přístupnost.
- Embeddings a anime/manga panel generation až po ověření základního workflow.
- **Hotovo, když:** hlavní scénáře lze provést přes UI bez ručního volání API.

## 7. Minimální testovací matice

1. Vytvoření série → postavy → příběhu → kapitoly.
2. Odmítnutí postavy nebo reference z jiné série.
3. Souběžné generování další kapitoly bez duplicitního čísla.
4. LLM timeout, 429, 500, prázdná a nevalidní odpověď.
5. Upload příliš velkého souboru, falešná přípona, poškozený obrázek a více souborů v jednom requestu.
6. Ověření přístupu k cizímu story/chapter/image/feedback/agent run.
7. Feedback s neplatným typem, extrémním časem a duplicitním hlasováním.
8. Agent trigger opakovaný současně, chyba během generování a bezpečné obnovení.
9. Migrace prázdné DB a upgrade existující DB.
10. Export/záloha a obnova dat bez ztráty obrázků nebo vazeb.

## 8. Definition of Done pro každou změnu

- Změna řeší konkrétní issue a má jasný rozsah.
- Přidán test pro nový scénář i relevantní regresi.
- Migrace jsou verzované a nedestruktivní.
- Žádné tajné údaje v kódu, testech ani logách.
- API chyby mají stabilní schéma a neodhalují interní výjimky.
- README a příklady konfigurace odpovídají skutečnému chování.
- CI je zelené; pokud test nebyl spuštěn, je to výslovně uvedeno.
- Funkční části se nepřepisují bez důvodu a změny se dodávají po malých reviewovatelných krocích.

## 9. Doporučený další krok

Nezačínat novými UI nebo embeddings. Nejdřív dokončit fázi A: získat kompletní inventuru, ověřit spuštění a testy. Potom opravit P0 bezpečnostní body a přidat regresní testy. Teprve po tom navázat migracemi, spolehlivostí agenta a Story Graphem.

## 10. Referenční zdroje

- FastAPI CORS: https://fastapi.tiangolo.com/tutorial/cors/
- OWASP File Upload Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- OWASP Input Validation Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
