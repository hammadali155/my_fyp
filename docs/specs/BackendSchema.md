# Backend Schema Document

## AI-Powered Classical Arabic & Quranic Learning Platform

**Version:** 1.0  
**Date:** 2026-03-25  
**Author:** Meher Ali (FA23-BCS-059)  
**Status:** Draft

---

## 1. Overview

PostgreSQL 15+ is the single source of truth. Redis holds sessions, hot SRS queues, and NLP result caches (no Redis persistence for canonical data).

All tables use:
- `BIGSERIAL` / `BIGINT` primary keys
- `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` updated by trigger where noted

Naming: `snake_case`. FKs: `{table}_id`.

---

## 2. Entity-Relationship Overview

```
users 1───n refresh_tokens
users 1───n decks
decks 1───n cards  n───1 words
users 1───n card_reviews  n───1 cards
users 1───n chat_sessions  n───1 chat_messages
users 1───n user_lessons  n───1 lessons
lessons n───n lessons (prerequisites via lesson_prerequisites)
users 1───n assessment_attempts
surahs 1───n verses 1───n words
words 1───n nahw_annotations (1:1 per word in corpus, but kept separate for flexibility)
users 1───n user_weak_areas  n───1 concept_tags
```

---

## 3. Tables (DDL)

### 3.1 Auth & Users

```sql
CREATE TABLE users (
    id               BIGSERIAL PRIMARY KEY,
    email            TEXT UNIQUE NOT NULL,
    name             TEXT NOT NULL,
    password_hash    TEXT NOT NULL,
    role             TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
    native_lang      TEXT NOT NULL DEFAULT 'en',
    ui_lang          TEXT NOT NULL DEFAULT 'en',
    level            TEXT NOT NULL DEFAULT 'beginner' CHECK (level IN ('beginner','intermediate','advanced')),
    learning_goal    TEXT,                  -- understand_quran | grammar | vocabulary
    streak_days      INTEGER NOT NULL DEFAULT 0,
    last_review_date DATE,
    xp               INTEGER NOT NULL DEFAULT 0,
    is_active        BOOLEAN NOT NULL DEFAULT true,
    onb_complete     BOOLEAN NOT NULL DEFAULT false,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE refresh_tokens (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_refresh_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_hash ON refresh_tokens(token_hash);
```

### 3.2 Quran Corpus

```sql
CREATE TABLE surahs (
    id               INTEGER PRIMARY KEY,          -- 1..114, matches mushaf number
    number           INTEGER NOT NULL UNIQUE,
    name_arabic      TEXT NOT NULL,
    name_translit    TEXT NOT NULL,
    name_english     TEXT NOT NULL,
    revelation_place TEXT CHECK (revelation_place IN ('meccan','medinan')),
    verse_count      INTEGER NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE verses (
    id              BIGSERIAL PRIMARY KEY,
    surah_id        INTEGER NOT NULL REFERENCES surahs(id),
    ayah_number     INTEGER NOT NULL,
    text_uthmani    TEXT NOT NULL,            -- full diacritics (Uthmanic)
    text_imlaei     TEXT,                     -- simplified spelling
    translation_en  TEXT,
    translation_ur  TEXT,
    word_count      INTEGER NOT NULL,
    UNIQUE (surah_id, ayah_number)
);
CREATE INDEX idx_verses_surah ON verses(surah_id);

CREATE TABLE words (
    id             BIGSERIAL PRIMARY KEY,
    verse_id       BIGINT NOT NULL REFERENCES verses(id) ON DELETE CASCADE,
    position       INTEGER NOT NULL,          -- 1-based position within ayah
    token          TEXT NOT NULL,             -- undiacritized form
    token_diacritized TEXT NOT NULL,          -- with harakaat
    root           TEXT NOT NULL,             -- three letters
    pattern        TEXT,                      -- morphological pattern / bab
    pos            TEXT,                      -- part of speech (from corpus tagging)
    gender          TEXT,
    number         TEXT,
    person          TEXT,
    tense          TEXT,                      -- past/present/imperative for verbs
    voice          TEXT,                      -- active/passive
    features_json  JSONB,                     -- raw CAMeL/corpus features (cat, lex, form_gen, etc.)
    lemma          TEXT,
    UNIQUE (verse_id, position)
);
CREATE INDEX idx_words_verse ON words(verse_id);
CREATE INDEX idx_words_root ON words(root);
CREATE INDEX idx_words_token ON words(token);

CREATE TABLE nahw_annotations (
    id           BIGSERIAL PRIMARY KEY,
    verse_id     BIGINT NOT NULL REFERENCES verses(id) ON DELETE CASCADE,
    word_id      BIGINT REFERENCES words(id) ON DELETE SET NULL,
    token_index  INTEGER NOT NULL,            -- position
    role         TEXT,                        -- فاعل / مفعول به / مبتدأ / خبر / نعت / حرف جر / ...
    dep_type     TEXT,                        -- raw dependency type (nsubj, dobj, ...)
    head_index   INTEGER,                     -- index of head token (or -1 if sentence root)
    irab         TEXT,                        -- grammatical case (رفع/نصب/جر/جزم)
    UNIQUE (verse_id, token_index)
);
CREATE INDEX idx_nahw_verse ON nahw_annotations(verse_id);
```

### 3.3 Knowledge & Curriculum

```sql
CREATE TABLE concept_tags (
    id         SERIAL PRIMARY KEY,
    slug       TEXT UNIQUE NOT NULL,          -- e.g. 'nouns-gender', 'verbal-sentence', 'fa'il'
    label_en   TEXT NOT NULL,
    label_ar   TEXT NOT NULL,
    module     TEXT NOT NULL CHECK (module IN ('sarf','nahw','vocabulary','balaghah'))
);

CREATE TABLE lessons (
    id           BIGSERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    module       TEXT NOT NULL CHECK (module IN ('sarf','nahw','vocabulary')),
    level        TEXT NOT NULL CHECK (level IN ('beginner','intermediate','advanced')),
    sequence     INTEGER NOT NULL,            -- ordering within level+module
    content_json JSONB NOT NULL,              -- sections: theory, examples, exercises, quiz
    est_minutes  INTEGER NOT NULL DEFAULT 15,
    UNIQUE (module, level, sequence)
);

CREATE TABLE lesson_prerequisites (
    lesson_id           BIGINT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    requires_lesson_id  BIGINT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    PRIMARY KEY (lesson_id, requires_lesson_id)
);

CREATE TABLE lesson_concept_tags (
    lesson_id  BIGINT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    concept_id INTEGER NOT NULL REFERENCES concept_tags(id) ON DELETE CASCADE,
    PRIMARY KEY (lesson_id, concept_id)
);

CREATE TABLE user_lessons (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id    BIGINT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    status       TEXT NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started','in_progress','completed')),
    score        NUMERIC(5,2),                -- 0-100
    completed_at TIMESTAMPTZ,
    UNIQUE (user_id, lesson_id)
);
CREATE INDEX idx_user_lessons_user ON user_lessons(user_id);

CREATE TABLE assessment_attempts (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score        INTEGER NOT NULL,            -- raw points
    placed_level TEXT NOT NULL CHECK (placed_level IN ('beginner','intermediate','advanced')),
    answers_json JSONB NOT NULL,              -- per-question responses
    completed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_assess_user ON assessment_attempts(user_id);

CREATE TABLE user_weak_areas (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id INTEGER NOT NULL REFERENCES concept_tags(id) ON DELETE CASCADE,
    weight     NUMERIC(5,2) NOT NULL DEFAULT 1.0,  -- normalized failing frequency
    last_seen  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, concept_id)
);
```

### 3.4 SRS / Spaced Repetition

```sql
CREATE TABLE decks (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    is_custom  BOOLEAN NOT NULL DEFAULT false,   -- false = built-in Quranic deck
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_decks_user ON decks(user_id);

CREATE TABLE cards (
    id            BIGSERIAL PRIMARY KEY,
    deck_id       BIGINT NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    word_id       BIGINT NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    status        TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','learning','review','mastered')),
    repetitions   INTEGER NOT NULL DEFAULT 0,
    ease_factor   NUMERIC(4,2) NOT NULL DEFAULT 2.50,   -- SM-2 EF, clamp [1.30, 3.00]
    interval_days INTEGER NOT NULL DEFAULT 0,
    due_date      DATE NOT NULL DEFAULT CURRENT_DATE,
    last_reviewed_at TIMESTAMPTZ,
    UNIQUE (deck_id, word_id)
);
CREATE INDEX idx_cards_due ON cards(due_date);
CREATE INDEX idx_cards_user_deck ON cards(deck_id, status);

-- join helper: cards → user via users.decks
CREATE INDEX idx_cards_deck ON cards(deck_id);
CREATE INDEX idx_cards_word ON cards(word_id);

CREATE TABLE card_reviews (
    id           BIGSERIAL PRIMARY KEY,
    card_id      BIGINT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    rating       INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),  -- SM-2 quality q
    response_ms  INTEGER,                       -- time to answer
    reviewed_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_reviews_card ON card_reviews(card_id);
CREATE INDEX idx_reviews_time ON card_reviews(reviewed_at);
```

### 3.5 AI Tutor

```sql
CREATE TABLE chat_sessions (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT NOT NULL DEFAULT 'New session',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_sessions_user ON chat_sessions(user_id);

CREATE TABLE chat_messages (
    id         BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
    content    TEXT NOT NULL,
    source_verse_ids BIGINT[],                  -- optionally cited verses (validated)
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_messages_session ON chat_messages(session_id);
```

### 3.6 Gamification (optional simple version)

```sql
CREATE TABLE badges (
    id      SERIAL PRIMARY KEY,
    slug    TEXT UNIQUE NOT NULL,
    label   TEXT NOT NULL,
    icon    TEXT,
    criteria_json JSONB NOT NULL               -- e.g. {"type":"streak","value":7}
);

CREATE TABLE user_badges (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id   INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    earned_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, badge_id)
);
```

---

## 4. Indexing Strategy

| Table | Index | Rationale |
|-------|-------|-----------|
| verses | (surah_id, ayah_number) UNIQUE | primary lookup |
| words | verse_id | join words→ayah |
| words | root | root-occurrence search (Sarf) |
| words | token | exact vocab lookups |
| nahw_annotations | verse_id | verse annotation fetch |
| cards | (deck_id, status) | SRS queue by status |
| cards | due_date | "due today" scans |
| card_reviews | reviewed_at | streak / retention stats |
| chat_messages | session_id | chat history fetch |
| refresh_tokens | token_hash | refresh validation |
| user_lessons | user_id | progress queries |

---

## 5. Query Patterns (Sample)

### Due review cards for a user
```sql
SELECT c.*
FROM cards c
JOIN decks d ON d.id = c.deck_id
WHERE d.user_id = $1
  AND c.due_date <= CURRENT_DATE
  AND c.status != 'mastered'
ORDER BY c.due_date ASC, c.repetitions ASC
LIMIT 100;
```

### Root occurrences (Sarf)
```sql
SELECT v.surah_id, v.ayah_number, w.token_diacritized, w.position
FROM words w
JOIN verses v ON v.id = w.verse_id
WHERE w.root = $1
ORDER BY v.surah_id, v.ayah_number, w.position;
```

### Verse annotation (Nahw)
```sql
SELECT w.id, w.position, w.token_diacritized, w.root, w.pattern, w.pos,
       n.role, n.dep_type, n.head_index, n.irab
FROM words w
LEFT JOIN nahw_annotations n ON n.verse_id = w.verse_id AND n.token_index = w.position
WHERE w.verse_id = $1
ORDER BY w.position;
```

### Unlock eligible lessons for a user
```sql
WITH completed AS (
  SELECT lesson_id FROM user_lessons
  WHERE user_id = $1 AND status = 'completed'
)
SELECT l.id, l.title, l.module, l.level, l.sequence
FROM lessons l
WHERE NOT EXISTS (
  SELECT 1 FROM lesson_prerequisites p
  WHERE p.lesson_id = l.id AND p.requires_lesson_id NOT IN (SELECT * FROM completed)
)
AND l.id NOT IN (SELECT * FROM completed)
ORDER BY l.level, l.module, l.sequence;
```

### Weak-area concepts feeding SRS
```sql
SELECT w.concept_id, c.slug, c.label_ar, w.weight
FROM user_weak_areas w
JOIN concept_tags c ON c.id = w.concept_id
WHERE w.user_id = $1 AND w.weight >= 0.5
ORDER BY w.weight DESC;
```

---

## 6. SM-2 Scheduler Implementation Contract

Server-side (authoritative). Client sends only `{ card_id, rating }`.

```python
def sm2_update(card, q: int):
    ef = float(card.ease_factor)
    if q < 3:
        card.repetitions = 0
        interval = 1
        ef = clamp(ef + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02), 1.30, 3.00)
    elif q == 3:
        interval = max(int(card.interval_days * 1.2), 1)
    elif q == 4:
        if card.repetitions == 0: interval = 1
        elif card.repetitions == 1: interval = 6
        else: interval = int(card.interval_days * ef)
        card.repetitions += 1
    else:  # q == 5
        if card.repetitions == 0: interval = 1
        elif card.repetitions == 1: interval = 6
        else: interval = int(card.interval_days * ef * 1.3)
        card.repetitions += 1
    card.ease_factor = ef
    card.interval_days = interval
    card.due_date = today + timedelta(days=interval)
    card.status = 'review' if card.repetitions >= 3 else ('learning' if card.repetitions > 0 else 'new')
```

Status rule: `new` → learning at first success → `review` when repetitions ≥ 3 → `mastered` when interval > 21 days (configurable).

---

## 7. Redis Keys

| Key | Type | TTL | Purpose |
|-----|------|-----|---------|
| `session:{jti}` | string (user_id JSON) | 15m | access-token session |
| `srs:due:{user_id}` | set | 30s | hot due-card ids snapshot |
| `sarf:{word}` | string JSON | 24h | analysis cache |
| `nahw:{hash(text)}` | string JSON | 24h | parse cache |
| `quran:verse:{verse_id}` | string JSON | 24h | verse+words+annotation bundle |
| `rl:{route}:{user_id}` | counter | window | rate limiting |
| `tutor:{session_id}:ctx` | string JSON | 15m | compact context for Gemini |

---

## 8. Migrations & Versioning

- Alembic is the migration tool; one migration file per change.
- Migrations are linear, forward-only in review; squash at release if messy.
- All DDL lives in migrations, NOT hand-applied.
- Seed data (`surahs`, `verses`, `words`, corpus annotations, lessons, concept_tags, badges) versioned as reproducible seed scripts with a `seed_version` marker row.

---

## 9. Constraints & Integrity Rules

1. `cards.word_id` must reference an existing corpus word → ensures Quranic grounding.
2. Nahw roles restricted to a canonical set + free-text fallback `dep_type` kept raw.
3. `users.email` unique; soft-delete via `is_active`, never hard-delete historically.
4. Rating values: `card_reviews.rating` ∈ 1..5 (1-2 fail, 3 hard, 4 good, 5 easy) — enforce CHECK.
5. `users.last_review_date` updated in the same transaction as the review to keep streak consistent.
6. Prerequisite graph must be acyclic — enforced by test, not DB (self-ref FK can't cycle-guard).

---

## 10. Open Schema Questions
1. Keep `nahw_annotations` separate from `words` or merge into `words`? Current design favors separation (corpus raw data isolated from derived fields).
2. Add nullable `parent_ayah` self-ref on `verses` for multi-ayah spans later? (defer)
3. `card_reviews.response_ms` nullable — keep or drop? (keep, enables retention analysis)
4. Do we need `quran_versions` table (Hafs/Warsh pressing) now? Defer — Hafs only in v1.