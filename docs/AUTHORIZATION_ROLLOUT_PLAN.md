# Authentication and ownership rollout plan

Status: proposed implementation plan, not implemented code.

## 1. Verified current state

The current API has no observed authentication dependency in the inspected routers. The series and image_folders models already contain nullable owner_id UUID columns, but there is no user model/table in the ORM model registry. FeedbackCreate accepts user_id from the request body. Stories and chapters are linked through Story.series_id and Chapter.story_id, so their effective owner can be derived through those relationships.

The project has an init_db.py script that calls SQLAlchemy Base.metadata.create_all; no Alembic configuration or versioned migrations directory was found in the audited tree. Existing records may already have null or arbitrary owner IDs. A naive foreign-key migration could therefore fail or accidentally make existing content inaccessible.

## 2. Security goals

- Require an authenticated identity for all data-changing and private content endpoints.
- Enforce ownership on the server for every series, story, chapter, character, image folder, image, feedback, and agent-run operation.
- Never trust a caller-supplied user_id as proof of identity.
- Keep /health public; keep OpenAPI access a deliberate deployment choice.
- Preserve existing content through an explicit legacy-data policy and a reversible, additive migration.
- Return consistent 401 responses for missing/invalid credentials and 404 for objects not found or not owned by the caller, avoiding resource enumeration.
- Keep local development usable without silently making production endpoints public.

## 3. Proposed implementation

### Identity and credentials
- Add a users table and SQLAlchemy model with UUID primary key, normalized unique email, password hash, active flag, and timestamps.
- Add register/login endpoints with strict request validation and generic login failure messages.
- Hash passwords with a maintained password-hashing implementation; never store or log plaintext passwords.
- Issue short-lived signed access tokens. Load signing secret and token lifetime from settings; production startup must fail if the secret is absent or insecure. Do not reuse the LLM API key as the token secret.
- Add a get_current_user dependency and a common ownership-check helper. Keep token parsing and ownership policy out of route handlers where possible.

### Ownership rules
- Series: Series.owner_id == current_user.id.
- Stories and chapters: resolve through Story.series_id and the parent series owner.
- Character anchors: resolve through CharacterAnchor.series_id.
- Image folders: use explicit folder owner; when associated with a series/story, validate that association belongs to the same user. Reject inconsistent series_id/story_id combinations.
- Images: resolve through Image.folder_id and its folder owner.
- Feedback: set user_id from the authenticated principal; remove or ignore the request-provided identity field in a documented compatibility step.
- Agent runs: resolve through the associated story and its series owner.
- List/search/inspiration endpoints must scope the SQL query by owner before applying user filters, not fetch broadly and filter in Python.

### Legacy-data migration
- First add migration tooling and a tested baseline/upgrade path without destructive schema recreation.
- Create the user table and keep the existing nullable ownership columns during rollout.
- Do not assign existing records to the first user who signs up. That would leak legacy data.
- Default policy: legacy records with no verifiable owner remain unavailable to ordinary users until an explicit one-time admin claim/import process assigns them.
- Back up the database before migration. Include a dry-run report listing counts of null, valid, and orphaned owner IDs.
- Add foreign keys only after existing owner IDs have been reconciled and the migration is verified against a copy of a real database.

### API compatibility
- Add authentication endpoints and dependencies in a staged PR.
- Update every router, including nested character, chapter, image, feedback, and agent routes; do not protect only the obvious CRUD endpoints.
- Update API documentation and .env.example with a generated secret placeholder and explicit local-development instructions.
- There is no frontend application in the audited repository, so document the bearer-token contract for external clients rather than inventing a frontend integration.

## 4. Required tests

1. Register, login, bad password, disabled user, malformed/expired token.
2. Unauthenticated requests to private endpoints fail; /health remains available.
3. User A cannot read, update, delete, generate for, or attach assets to User B's series/story/chapter/folder.
4. List, filter, inspiration, feedback summaries, and agent history cannot leak cross-user rows.
5. Caller-supplied user_id cannot impersonate another user.
6. Inconsistent series/story folder associations are rejected.
7. Migration tests preserve existing rows and report unowned/orphaned legacy records without granting them to a new account.
8. All tests run with an isolated PostgreSQL service; SQLite-only tests are insufficient for PostgreSQL UUID/JSONB/array semantics.

## 5. Rollout order

1. Introduce Alembic configuration and establish a safe baseline strategy for existing installations.
2. Add the user model, migration, password hashing, token issuance, and unit tests.
3. Add the current-user dependency and ownership helpers.
4. Protect routes in small groups and add cross-user isolation tests for each group.
5. Reconcile legacy records and add ownership foreign keys only after the dry run.
6. Harden Docker Compose: bind development service ports to loopback by default and replace reusable hard-coded credentials with documented environment variables.
7. Require a successful CI run and a migration rehearsal against a database copy before merging enforcement.

## 6. Explicit non-goals for the first pass

- OAuth/social login, roles/teams, billing, public sharing links, and refresh-token rotation.
- Automatically claiming existing content for whichever user signs up first.
- Treating UUIDs as access control. IDs are identifiers, not authorization.
