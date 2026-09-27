# Important Links, Datasets & Research Resources
**Project: Jawhar (جوهر) — AI-Powered Classical Arabic & Quranic Learning Platform**

This document serves as the authoritative research and technical resource index for the Jawhar project, covering open datasets, NLP toolkits, memory algorithms, benchmarks, LLM safety mechanisms, and academic references.

---

## 1. Quranic Corpora & Primary Datasets

| Resource | Description & Utility | Link / Reference |
| :--- | :--- | :--- |
| **Tanzil Quran Project** | Verified Uthmani text with precise diacritics (tashkeel), pause marks (waqf), and translations across 40+ languages (English: Sahih International, Yusuf Ali, Arberry; Urdu: Maududi, Jalandhari). Used as our ground truth text. | [tanzil.net](https://tanzil.net) / [tanzil.net/download](https://tanzil.net/download) |
| **Quranic Arabic Corpus (QAC)** | University of Leeds project by Kais Dukes. Morphological annotations for ~77,430 words (root, lemma, POS, stem, affixes). Traditional Arabic grammar framework. Covers ~40% of deep syntax. | [corpus.quran.com](https://corpus.quran.com) |
| **Extended Quranic Treebank (EQTB)** | Modern comprehensive treebank (LREC-COLING 2024). 132,736 tokens, 43-column CoNLL-X format, 140 classical I'rab dependency labels, covering 100% of the Quran with parallel Uthmani & Imlaai orthography and TAQDIR elliptical resolution module. | [EQTB Paper (LREC-COLING 2024)](https://aclanthology.org/2024.lrec-main.422/) / [HuggingFace Dataset](https://huggingface.co/datasets) |
| **Quran.com API v4** | REST API providing verses, translations, audio recitations (by word and ayah), glyphs, word-by-word timestamps, and tafsir metadata. | [quran.api-docs.io](https://quran.api-docs.io/v4) / [github.com/quran/quran.com-api](https://github.com/quran/quran.com-api) |
| **QurSim Dataset** | Semantic similarity dataset for Quranic verse pairs, useful for evaluating semantic relatedness and verse recommendations. | [QurSim on GitHub / PapersWithCode](https://paperswithcode.com/dataset/qursim) |

---

## 2. Arabic NLP & Morphological Toolkits

| Tool | Focus & Architecture | Key Documentation & Repos |
| :--- | :--- | :--- |
| **CAMeL Tools** | State-of-the-art Python toolkit from CAMeL Lab (NYUAD / CMU). Provides morphological analysis, disambiguation, root extraction, lemmatization, POS tagging, and diacritization for Classical and Modern Arabic. | [camel-tools.readthedocs.io](https://camel-tools.readthedocs.io) / [github.com/CAMeL-Lab/camel_tools](https://github.com/CAMeL-Lab/camel_tools) |
| **Farasa** | Ultra-fast Arabic segmenter, POS tagger, and dependency parser developed by QCRI/KACST. Excels at clitic boundary identification (prefixes like *fa-, wa-, bi-*, suffixed pronouns) and dependency parsing. Available via Java CLI, REST, and Python wrappers. | [farasa.qcri.org](http://farasa.qcri.org) / [github.com/qcri/farasa](https://github.com/qcri/farasa) |
| **MADAMIRA** | Morphological analyzer and disambiguator from Columbia & NYUAD. Combines SVM and n-gram language models to yield 13 inflectional/clitic features with high accuracy. | [MADAMIRA NYUAD](https://camel.abudhabi.nyu.edu/madamira-and-mada/) |
| **PyArabic** | Lightweight Python library for Arabic language processing: tashkeel normalization, harakat stripping, shadda handling, and character classifications. | [pyarabic.readthedocs.io](https://pyarabic.readthedocs.io) / [github.com/linuxscout/pyarabic](https://github.com/linuxscout/pyarabic) |
| **AraBERT / CamelParser** | Pretrained BERT transformers specialized for Arabic NLP and syntax parsing. Used for high-accuracy contextual embedding and syntactic relation extraction. | [github.com/aub-mind/arabert](https://github.com/aub-mind/arabert) |

---

## 3. Spaced Repetition Algorithms (SRS)

| Algorithm / Library | Mechanics & Mathematical Foundation | Implementation Reference |
| :--- | :--- | :--- |
| **FSRS (Free Spaced Repetition Scheduler v5/v6)** | Modern ML-based scheduling modeling Memory Stability ($S$), Retrievability ($R = e^{\ln(0.9) \cdot t / S}$), and Difficulty ($D$). Delivers 20–30% fewer reviews than SM-2 at identical or higher target retention (80–90%). | [github.com/open-spaced-repetition/fsrs4anki](https://github.com/open-spaced-repetition/fsrs4anki) / [py-fsrs on PyPI](https://pypi.org/project/py-fsrs/) / [fsrs-kotlin](https://github.com/open-spaced-repetition/fsrs-rs) |
| **SuperMemo SM-2** | Industry standard baseline algorithm using static interval multipliers and ease factors ($EF' = EF + (0.1 - (5-q) \cdot (0.08 + (5-q) \cdot 0.02))$). Serves as our comparative baseline. | [SuperMemo SM-2 Description](https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method) |

---

## 4. LLM Tutoring, Benchmarks & Safety Safeguards

| Benchmark / Tool | Purpose & Performance | Key Resources |
| :--- | :--- | :--- |
| **Gemini 2.0 / 3.0 Flash API** | High-speed, high-reasoning foundation model with strong multilingual and Arabic capabilities. Benchmark leader on the Quran track of IslamicMMLU (scoring >99%). | [ai.google.dev](https://ai.google.dev) / [Google AI Studio](https://aistudio.google.com) |
| **IslamicMMLU Benchmark** | Standardized benchmark assessing LLMs across Quran, Hadith, and Fiqh domains to evaluate theological and linguistic accuracy. | [IslamicMMLU on HuggingFace / arXiv](https://arxiv.org/abs/2406.00000) |
| **IslamicEval 2025** | Shared task and dataset focused on hallucination detection and quotation verification in Islamic texts generated by LLMs. Grounding for our RAG verification pipeline. | [ArabicNLP 2025 Shared Tasks](https://arabicnlp2025.github.io) |
| **Hybrid RAG Pipeline** | Tanzil text exact matching via BM25/TF-IDF combined with dense bi-encoder embeddings and cross-encoder rerankers to ensure 0% hallucinated verse citations in AI tutor responses. | [Haystack / LangChain Hybrid Search](https://docs.haystack.deepset.ai) |

---

## 5. Pedagogical Curricula & Language Standards

| Curriculum | Pedagogical Approach & Structure | Alignment in Jawhar |
| :--- | :--- | :--- |
| **Bayyinah "Dream" Program (Ustadh Nouman Ali Khan)** | Focuses on functional grammar directly applied to the Quran: Nahw 1-2 (Sentence foundations, Ism characteristics, Harf, Fi'l), Sarf 3-4 (10 verb families, Awzan, root transformations), Intermediate/Balaghah (rhetoric). | Directly guides our structured lesson progression and interactive drills. |
| **Zaytuna College Arabic Curriculum** | Academic standard based on classical Arabic texts and the *Al-Kitaab* framework (Nominal sentences, Idafa, Nisba, Verbal moods, Masdar, Case endings). | Guides our assessment bank and CEFR-equivalent level placement criteria. |
| **Madinah Arabic Books (Dr. V. Abdur Rahim)** | World-renowned Classical Arabic pedagogy emphasizing gradual syntactic construction and real-world linguistic patterns. | Provides exercises and progressive difficulty grading for beginner learners. |

---

## 6. Frontend & Typography Resources

| Tool | Application & Details | Link |
| :--- | :--- | :--- |
| **Amiri Font (Amiri Quran)** | Classical Naskh typeface digitized by Khaled Hosny, crafted specifically for Quranic and Classical Arabic typesetting with full support for complex vocalization and diacritic stacking. | [Google Fonts Amiri](https://fonts.google.com/specimen/Amiri) / [amirifont.org](https://amirifont.org) |
| **Noto Naskh Arabic** | Google Fonts typography providing exceptional legibility across varied device screen resolutions for UI elements and explanations. | [Google Fonts Noto Naskh Arabic](https://fonts.google.com/specimen/Noto+Naskh+Arabic) |
| **Compose Multiplatform RTL** | JetBrains Compose Multiplatform bidirectional and right-to-left layout guidelines for seamless Arabic reading and navigation. | [JetBrains Compose Multiplatform Docs](https://www.jetbrains.com/help/kotlin-multiplatform-dev/compose-multiplatform.html) |
