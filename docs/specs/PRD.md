# Product Requirements Document (PRD)

## AI-Powered Classical Arabic & Quranic Learning Platform

**Version:** 1.0  
**Date:** 2026-03-25  
**Author:** Meher Ali (FA23-BCS-059)  
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Product Vision
Build an AI-powered cross-platform learning platform that enables self-paced learners to develop Classical Arabic proficiency through the Quran, integrating three core AI modules: Sarf (morphology) engine, Nahw (syntax) parser, and an intelligent AI Tutor, backed by spaced-repetition vocabulary and personalized learning paths.

### 1.2 Problem Statement
- **Shallow depth:** Existing vocabulary apps (Quranic, Kalaam) teach words but not grammar/morphology
- **Accessibility gap:** corpus.quran.com is researcher-oriented, desktop-only, no AI tutor
- **Cost/scalability:** Teacher-led platforms (Buruj, Kalimah) are expensive and synchronous
- **Wrong dialect:** General Arabic apps (Duolingo, Mondly) teach MSA, not Classical Quranic Arabic

### 1.3 Target Audience
- **Primary:** Self-paced Muslim learners (ages 15-50) wanting to understand Quranic Arabic
- **Secondary:** Islamic studies students, Arabic language enthusiasts, converts to Islam
- **Tertiary:** Educators seeking supplementary tools for Classical Arabic instruction

### 1.4 Success Metrics
| Metric | Target |
|--------|--------|
| Morphological accuracy (vs corpus.quran.com) | ≥ 90% |
| User retention (7-day) | ≥ 40% |
| User retention (30-day) | ≥ 20% |
| Learning gain (pre/post test) | ≥ 30% improvement |
| AI Tutor quality (expert rating) | ≥ 4.0/5.0 |
| Daily active users (Month 6) | ≥ 500 |

---

## 2. Core Features

### 2.1 Sarf Engine (Morphology Analyzer)
**Priority:** P0 (Must Have)

**User Stories:**
- As a learner, I want to enter any Arabic word and see its 3-letter root, morphological pattern, and grammatical features
- As a learner, I want to see all Quranic verses containing a specific root
- As a learner, I want to view full conjugation tables for verbs

**Functional Requirements:**
| ID | Requirement | Details |
|----|-------------|---------|
| FR-SARF-01 | Root extraction | Extract 3-letter root (جذر) from any Arabic word using CAMeL Tools |
| FR-SARF-02 | Pattern identification | Identify morphological pattern (باب) and verb form (I-X) |
| FR-SARF-03 | Grammatical features | Display tense, voice, gender, number, person |
| FR-SARF-04 | Conjugation table | Generate full paradigm for identified verb/noun |
| FR-SARF-05 | Quranic occurrences | List all verses containing the root with highlighting |
| FR-SARF-06 | Diacritization | Auto-diacritize input word using MADAMIRA/Farasa |

**Acceptance Criteria:**
- Process word in < 2 seconds
- Accuracy ≥ 90% vs corpus.quran.com gold standard (500-word test set)
- Handle clitics (prefixed particles, suffixed pronouns)

### 2.2 Nahw Parser (Syntax Annotator)
**Priority:** P0 (Must Have)

**User Stories:**
- As a learner, I want to input a Quranic ayah and see grammatical roles color-coded inline
- As a learner, I want to tap a word and see its Nahw analysis (فاعل، مفعول به، مبتدأ، خبر، etc.)
- As a learner, I want to see the dependency tree for a sentence

**Functional Requirements:**
| ID | Requirement | Details |
|----|-------------|---------|
| FR-NAHW-01 | POS tagging | Tag each word with part-of-speech using Farasa/CAMeL Tools |
| FR-NAHW-02 | Dependency parsing | Identify head-dependent relations |
| FR-NAHW-03 | Nahw role mapping | Map dependencies to classical terms (فاعل، مفعول، مبتدأ، خبر، نعت، ظرف، حال، تميير، مستثنى) |
| FR-NAHW-04 | Color-coded UI | Inline annotation with distinct colors per role |
| FR-NAHW-05 | Interactive details | Tap/click word for detailed grammatical breakdown |
| FR-NAHW-06 | Tree visualization | Display dependency tree for sentence |

**Acceptance Criteria:**
- Parse Quranic ayah in < 3 seconds
- Coverage: All 77,430 Quranic words (via corpus.quran.com dataset)
- Accuracy ≥ 85% for Nahw role assignment (expert evaluation)

### 2.3 AI Tutor (Conversational Assistant)
**Priority:** P0 (Must Have)

**User Stories:**
- As a learner, I want to ask grammar questions and get Quranic examples
- As a learner, I want the tutor to quiz me on concepts I've learned
- As a learner, I want explanations tailored to my current level

**Functional Requirements:**
| ID | Requirement | Details |
|----|-------------|---------|
| FR-TUTOR-01 | Grammar Q&A | Answer Classical Arabic grammar questions with Quranic evidence |
| FR-TUTOR-02 | Morphological breakdown | Explain word formation on demand (root + pattern) |
| FR-TUTOR-03 | Verse explanation | Provide grammatical analysis of any Quranic ayah |
| FR-TUTOR-04 | Adaptive quizzing | Generate level-appropriate practice questions |
| FR-TUTOR-05 | Context awareness | Remember user's learning path, weak areas, and progress |
| FR-TUTOR-06 | Pedagogical prompt | System prompt engineered with Nahw/Sarf terminology and progression |

**Technical Specs:**
- Model: Gemini 2.0 Flash API
- Temperature: 0.3 (factual consistency)
- Context window: Full conversation history + user profile
- Rate limiting: 60 requests/minute per user

**Acceptance Criteria:**
- Response latency < 5 seconds
- Expert rating ≥ 4.0/5.0 on relevance, accuracy, pedagogical clarity
- Zero hallucinated Quranic references (verified against corpus)

### 2.4 Vocabulary SRS (Spaced Repetition System)
**Priority:** P0 (Must Have)

**User Stories:**
- As a learner, I want daily review sessions with words I'm about to forget
- As a learner, I want to see Quranic context for each vocabulary word
- As a learner, I want streak tracking and mastery badges

**Functional Requirements:**
| ID | Requirement | Details |
|----|-------------|---------|
| FR-SRS-01 | SM-2 algorithm | Implement SuperMemo SM-2 with ease factor, interval, repetition |
| FR-SRS-02 | Quranic flashcards | Each card: word, root, translation, Quranic example ayah, audio |
| FR-SRS-03 | Scheduling | Daily review queue prioritized by forgetting threshold |
| FR-SRS-04 | Mastery tracking | Per-word mastery level (New → Learning → Review → Mastered) |
| FR-SRS-05 | Streaks & gamification | Daily streak counter, XP, badges for milestones |
| FR-SRS-06 | Custom decks | User-created decks from Sarf/Nahw module discoveries |

**Acceptance Criteria:**
- Retention rate ≥ 80% at 30-day interval (vs control group)
- Daily review session ≤ 15 minutes for 50 cards
- Offline-capable review (cached cards)

### 2.5 Adaptive Learning Path
**Priority:** P1 (Should Have)

**User Stories:**
- As a new user, I want an assessment to determine my starting level
- As a learner, I want lessons to unlock as I demonstrate competency
- As a learner, I want weak areas to resurface automatically

**Functional Requirements:**
| ID | Requirement | Details |
|----|-------------|---------|
| FR-PATH-01 | Onboarding assessment | 20-question diagnostic covering Sarf/Nahw/vocabulary |
| FR-PATH-02 | Level placement | Map score to Bayyinah-style levels (Beginner/Intermediate/Advanced) |
| FR-PATH-03 | Curriculum unlocking | Sequential lesson unlocking based on competency thresholds |
| FR-PATH-04 | Weakness detection | Track error patterns, flag struggling concepts |
| FR-PATH-05 | Remedial resurfacing | Auto-inject review of weak areas into learning path |
| FR-PATH-06 | Progress dashboard | Visual progress map with completed/locked/available lessons |

**Acceptance Criteria:**
- Assessment completion < 10 minutes
- Placement accuracy validated by expert review
- 80% of users advance at least one level in 4 weeks

---

## 3. Non-Functional Requirements

### 3.1 Performance
| Requirement | Target |
|-------------|--------|
| API response time (p95) | < 500ms |
| Sarf/Nahw processing | < 3s |
| AI Tutor response | < 5s |
| Page load (web) | < 2s |
| App launch (mobile) | < 3s |
| Concurrent users | 1,000+ |

### 3.2 Reliability
- Uptime: 99.5% (excluding planned maintenance)
- Data backup: Daily automated PostgreSQL backups
- Error rate: < 0.1% for critical user flows

### 3.3 Security
- JWT-based authentication with refresh tokens
- bcrypt password hashing (cost factor 12)
- Rate limiting: 100 req/min (auth), 60 req/min (AI)
- HTTPS everywhere, HSTS, CSP headers
- No PII in logs

### 3.4 Accessibility
- WCAG 2.1 AA compliance
- Arabic RTL support throughout
- Screen reader compatible
- Adjustable font sizes
- High contrast mode

### 3.5 Localization
- Primary: Arabic (RTL) + English (LTR)
- Quranic text: Uthmanic script with optional diacritics
- UI translations: Arabic, English (extensible)

---

## 4. User Flows

### 4.1 Primary Flow: Learn a New Concept
1. User opens app → Dashboard shows next lesson
2. User starts lesson → Interactive Sarf/Nahw explanation with Quranic examples
3. User practices → Guided exercises with instant feedback
4. User completes → Vocabulary cards added to SRS queue
5. User reviews → Daily SRS session reinforces learning

### 4.2 Secondary Flow: Analyze a Word/Verse
1. User opens Sarf Engine or Nahw Parser
2. User inputs word/ayah (Arabic keyboard or paste)
3. System analyzes → Displays results with visual annotations
4. User explores → Taps for details, adds to custom deck
5. User asks AI Tutor → Follow-up questions on the analysis

### 4.3 Tertiary Flow: AI Tutor Conversation
1. User opens Chat → Greeted with context-aware prompt
2. User asks question → Tutor responds with Quranic examples
3. User requests quiz → Tutor generates practice
4. User ends session → Summary saved to learning history

---

## 5. Data Requirements

### 5.1 Quranic Corpus
- **Source:** Quran.com API + corpus.quran.com dataset
- **Content:** 6,236 verses, 77,430 words, word-level morphology
- **License:** Open for educational use (verify per source)

### 5.2 Linguistic Data
- **CAMeL Tools:** Morphological analyzer, disambiguator
- **Farasa:** POS tagger, dependency parser
- **MADAMIRA:** Diacritization (optional enhancement)

### 5.3 User Data
- Progress, SRS schedules, preferences, chat history
- GDPR-compliant: export, delete, consent management

---

## 6. Constraints & Assumptions

### 6.1 Technical Constraints
- Single FastAPI backend serving all clients (web + mobile)
- CAMeL Tools requires Python 3.8+ with specific dependencies
- Gemini API requires paid tier for production usage
- Kotlin Multiplatform + Compose Multiplatform shared UI (Android / iOS / Desktop / Web-Wasm); Web-Wasm is the stretch target

### 6.2 Timeline Constraints
- FYP deadline: August 2026 (6 months from March)
- Demo required for defense presentation
- Evaluation with 30 participants in Month 5-6

### 6.3 Budget Constraints
- Student project budget (minimal cloud costs)
- Vercel free tier + Google Cloud Run free tier
- Gemini API: estimate $20-50/month for evaluation phase

### 6.4 Assumptions
- Quran.com API remains stable and accessible
- CAMeL Tools/Farasa models sufficient for Quranic Arabic
- 30 participants recruitable from COMSATS/GDGoC community
- Supervisor approval for methodology

---

## 7. Out of Scope (v1.0)
- Teacher dashboard / classroom management
- Live tutoring with human instructors
- Audio recitation / tajweed feedback
- Social features (leaderboards, friends, groups)
- Offline-first mobile (online required for AI/NLP)
- Multiple Quranic readings (Qira'at) - Hafs only initially
- Balaghah (rhetoric) module
- Speech-to-text for pronunciation

---

## 8. Dependencies

| Dependency | Type | Risk |
|------------|------|------|
| Quran.com API | External | Medium (rate limits, stability) |
| corpus.quran.com dataset | External | Low (static download) |
| CAMeL Tools | Open source | Low (mature library) |
| Farasa | Open source | Medium (Java-based, integration) |
| Gemini 2.0 Flash API | Commercial | Medium (pricing, quotas) |
| PostgreSQL/Redis | Infrastructure | Low (managed services) |

---

## 9. Release Criteria

### 9.1 MVP (Month 4)
- [ ] User auth + dashboard
- [ ] Sarf Engine functional
- [ ] Basic SRS with SM-2
- [ ] KMP client deployed (Android + Desktop; Web-Wasm as stretch)

### 9.2 Beta (Month 5)
- [ ] Nahw Parser functional
- [ ] AI Tutor integrated
- [ ] KMP mobile app (Android + iOS via Compose Multiplatform)
- [ ] Learning path + assessment

### 9.3 Release Candidate (Month 6)
- [ ] All evaluation studies complete
- [ ] Performance targets met
- [ ] Security audit passed
- [ ] Documentation complete

---

## 10. Appendix

### 10.1 Glossary
| Term | Definition |
|------|------------|
| Sarf | Arabic morphology (word formation, roots, patterns) |
| Nahw | Arabic syntax (grammatical roles, sentence structure) |
| I'rab | Grammatical case inflection (nominative, accusative, genitive) |
| Jidhr | Three-letter root (جذر) |
| Bab | Morphological pattern/verb form (باب) |
| SM-2 | SuperMemo 2 spaced repetition algorithm |

### 10.2 References
- [1] Dukes & Buckwalter (2010). Quranic Dependency Treebank. LREC.
- [2] Obeid et al. (2020). CAMeL Tools. LREC.
- [3] Abdelali et al. (2016). Farasa. NAACL-HLT.
- [4] Wozniak (1990). SM-2 Algorithm. SuperMemo.