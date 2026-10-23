# Fáze A — inventura repozitáře AI Story Forge

Datum kontroly: 2026-10-24  
Kontrolovaná větev: `main` (commit `ecc83c55c75be170306fe81ebaf58b612dec0ac7`)  
Metoda: GitHub file tree, čtení zdrojových souborů, kontrola GitHub Actions logu. Aplikace nebyla v tomto prostředí lokálně klonována ani spuštěna; ověřený běh CI uveden zvlášť.

## Shrnutí

Repozitář je malý backendový prototyp ve FastAPI. Obsahuje modely sérií, postav, příběhů, kapitol, obrázků, feedbacku a běhů agenta; routery pro tyto oblasti; služby generování příběhu, LLM klienta, lokálního úložiště a engagement skóre; SQL schema; Docker Compose a bootstrap skript.

Při této inventuře bylo ve stromu `main` nalezeno přibližně 48 souborů. Nejsou zde nalezeny soubory frontendové aplikace, adresář testů, `environment.yml` ani adresář Alembic migrací. Jde o stav stromu v kontrolovaném commitu; neznamená to, že tyto funkce nejsou plánované.

## Ověřená zjištění

### A1 — CI selhávalo kvůli neexistujícímu environment.yml (potvrzeno logem)

Workflow `.github/workflows/python-package-conda.yml` spouštěl:

```bash
conda env update --file environment.yml --name base
```

V hlavní větvi `environment.yml` není. Log posledního běhu `40023651521` obsahuje chybu `EnvironmentFileNotFound` a kroky lintování a pytest byly přeskočeny.

**Náprava navržena a ověřena v PR #3:** instalace přes `pip install -r apps/api/requirements.txt pytest flake8`, Python 3.11, lint a smoke testy. GitHub Actions běh pro PR #3 skončil úspěšně: https://github.com/smusCZ/ai-story-forge/actions/runs/40032279811. PR #3 je při sepsání této zprávy otevřený; změna zatím není součástí `main`.

### A2 — Patch soubor obsahuje opravy, které nejsou aplikovány

Soubor `0001-fix-api-changes.txt` obsahuje unified diff s navrženými změnami pro CORS, výchozí DEBUG, uploady, číslování kapitol a engagement. Kontrola aktuálních souborů `apps/api/app/main.py`, `apps/api/app/core/config.py` a `apps/api/app/services/storage.py` potvrzuje, že odpovídající změny nejsou ve zdrojovém kódu `main` aplikovány. PR #2 byl sloučen, ale to samo o sobě neznamená, že se patch z textového souboru aplikoval.

Doporučení: neaplikovat celý patch naslepo; rozdělit jej na malé změny s testy. Po úspěšné aplikaci zvážit odstranění patch souboru nebo přesun do historie změn.

### A3 — Bezpečnost a vlastnictví dat (P0 před internetovým/multi-user provozem)

- Routery série a příběhů neukazují autentizaci ani filtrování podle vlastníka.
- Modely `Series` a `ImageFolder` obsahují nullable `owner_id`, ale strom nemá model uživatele ani tabulku users a v kontrolovaných routerech není vynucováno vlastnictví.
- Feedback přijímá `user_id` z requestu; není vázán na ověřenou identitu.
- `main.py` nastavuje CORS `allow_origins=["*"]` a `allow_credentials=True`.
- `config.py` má `debug=True` jako výchozí hodnotu.
- Docker Compose používá pevné vývojové přihlašovací údaje a publikuje porty DB/Redis/MinIO.

Doporučení: před veřejným nasazením zvolit explicitně režim local-only nebo implementovat autentizaci a autorizaci. Do té doby nesměřovat prototyp na veřejnou síť s reálnými uživatelskými daty.

### A4 — Upload a servírování souborů

`storage.py` čte celý soubor do paměti a limit 15 MB kontroluje až poté; povolení formátu je založeno na příponě. `main.py` servíruje statický adresář z pevně zapsané cesty `/tmp/ai-story-forge/uploads`, zatímco služba storage čte `UPLOAD_ROOT` z prostředí. Tyto cesty se mohou rozcházet.

Doporučení: limitovat request před načtením, streamovat po blocích, validovat skutečný formát, sjednotit konfiguraci upload root a rozhodnout, zda mají být soubory veřejné nebo autorizované.

### A5 — Databázové schéma se může rozcházet

- `packages/db/schema.sql` definuje sloupec `images.embedding vector(768)`, zatímco ORM model `Image` tento sloupec nemá.
- `chapters.branch_id` je nullable a není navázán na samostatnou tabulku větví.
- Unikátní omezení `(story_id, chapter_number, branch_id)` v PostgreSQL nebrání duplicitám pro NULL `branch_id` při výchozí sémantice NULL. Patch soubor zmiňuje `NULLS NOT DISTINCT`, ale ORM model stále používá obyčejný `UniqueConstraint`.
- `scripts/init_db.py` používá `Base.metadata.create_all`; ve stromu nebyl nalezen adresář verzovaných Alembic migrací.
- Pole `CharacterAnchor.reference_image_ids` je pole UUID, ne relace s cizím klíčem.

Doporučení: definovat jeden zdroj pravdy pro schéma, zavést Alembic migrace a rozhodnout o explicitních pravidlech pro nullable unique klíče, větve a reference obrázků.

### A6 — Integrita vazeb mezi složkou, sérií a příběhem

`images.py` kontroluje, zda zadaná série a příběh existují, ale v kontrolovaném kódu není doloženo, že příběh patří do stejné série jako složka. Je možné vytvořit rozpornou kombinaci `series_id` a `story_id`, pokud endpoint přijme oba údaje.

Doporučení: definovat invarianty pro složky a vynutit je aplikační validací i databázovými omezeními, kde to jde.

### A7 — Výjimky a hranice LLM

Routery kapitol a agenta zachytávají obecné `Exception` a vracejí klientovi text výjimky. LLM klient má timeout 120 sekund a vrací `choices[0].message.content` bez samostatné validace strukturovaného výstupu.

Doporučení: stabilní chybové schéma a korelační ID, interní detaily pouze v serverových logách, validovaný výstupní model a omezené retry.

### A8 — Feedback může chybně zpracovat některé hodnoty času

`compute_chapter_summary` filtruje `time_spent` přes `content.replace(".", "").isdigit()`, poté hodnotu převádí na float. Vstup jako `1.2.3` může projít filtrem a selhat při konverzi. Chybí také doložený horní limit a sémantická validace času.

Doporučení: validovat `time_spent` jako číselné pole v Pydantic schématu, s konečným rozsahem a explicitní jednotkou.

### A9 — Dokumentace a aktuální implementace

README popisuje funkce a API flow, ale stav `[x]` označuje existenci implementace, ne důkaz integrační funkčnosti. Plné větvení, frontend, automatický scheduling, embeddings a generování panelů jsou výslovně neuvedené jako dokončené. Dokumentace by měla rozlišovat implementováno, testováno a plánováno.

## Doporučené pořadí dalších kroků

1. Sloučit PR #3 až po kontrole zeleného CI; pak ověřit, že `main` má skutečně funkční workflow.
2. Rozdělit opravy z `0001-fix-api-changes.txt` do malých PR: nejdříve bezpečné defaulty/CORS, uploady, bezpečné chyby, číslování kapitol a engagement.
3. Přidat testovací PostgreSQL a integrační testy pro sérii → postavy → příběh → kapitola, chybné vazby, souběžné generování a upload.
4. Zavést Alembic a ověřit rozdíly mezi ORM a `packages/db/schema.sql`.
5. Teprve potom řešit autorizaci více uživatelů nebo výslovně uzamknout MVP jako lokální single-user prototyp.
6. Následně navrhnout skutečné větve a verzování kapitol; teprve na tomto základě stavět Story Graph a dlouhodobou paměť.

## Co je ověřeno a co nikoli

**Ověřeno:** struktura souborů aktuálního commitu, obsah kontrolovaných souborů, přesná příčina posledního selhání CI a úspěšný GitHub Actions běh pro PR #3.

**Neověřeno:** lokální start celého stacku s PostgreSQL/Redis/MinIO, úplná funkčnost všech API endpointů, testy s reálnou databází, bezpečnostní sken závislostí a produkční deployment. Úspěšný smoke test v PR #3 nenahrazuje integrační ani bezpečnostní testy.
