---
# ============================================================
# ALEX TAN — CONSOLIDATED APPLICATION PROFILE
# Source of truth for job suitability assessment and
# generating tailored resumes, cover letters, and messages.
#
# HOW TO USE:
#   • All fields are filled. Remaining [FILL IN] tags mark
#     information intentionally deferred (e.g. outcomes not
#     yet known).
#   • Proficiency scale:
#     Expert   = Can lead, teach, and solve complex problems independently
#     Working  = Can build and debug independently
#     Familiar = Have used; comfortable with basics
# ============================================================

profile:
  name: Alex Tan
  email: alex.tan.demo@example.com
  phone: "+65 8123 4567"
  linkedin: linkedin.com/in/alex-tan-demo
  github: github.com/alex-tan-demo
  location: Singapore
  work_authorisation: Singapore Citizen
  availability: Immediately
  languages_spoken:
    - English (fluent)
    - Mandarin (working proficiency)

# ── JOB SEARCH FILTERS ─────────────────────────────────────

search_filters:
  employment_type:
    - Full-time
    - Internship
  location:
    - Singapore (Hybrid)
    - Singapore (On-site)
    - Singapore (Remote)
    - open_to_relocation: true # confirm once relevant
  salary_floor_sgd_monthly: 4800
  salary_note: "Open to negotiation; prioritise role fit, growth potential, and research depth"
  experience_level: Entry-level / Fresh graduate (<1 year relevant experience)
  recency_priority: true   # Only listings posted within last 5 days AND closing date in the future
  keywords_to_exclude:
    - Sales Engineer
    - Hardware Engineer
    - Pure Frontend (no AI/data component)
    - e-commerce / retail (unless AI research role)
  title_prefixes_to_exclude:   # Skip any listing whose title starts with or contains these
    - Senior
    - Lead
    - Principal
    - Manager
    - Head of
    - AVP
    - VP
    - Director

# ── SEARCH TARGETING ───────────────────────────────────────
# Consumed by tools/search_mcf.py (queries + filters) so search behaviour
# lives here with every other preference — not hardcoded in a tool.
# Updated via workflow 01's Gather Notes feedback phase (approved edits only).

search_targeting:
  max_years_experience: 1       # skip listings requiring more
  recency_days: 5               # skip listings posted earlier than this — strict, freshness matters
  target_count: 5               # stop gathering once this many qualifying URLs are added per run
  # salary floor comes from search_filters.salary_floor_sgd_monthly above
  excluded_title_words:
    [senior, lead, principal, manager, head, avp, vp, director, chief,
     staff, postdoctoral, postdoc]
  excluded_title_substrings:    # case-insensitive substring match
    - "(phd)"
    - "phd graduate"
  mcf_queries:
    - ML AI NLP LLM Computer Vision research engineer
    - ML AI engineer entry
    - NLP LLM engineer entry
    - computer vision engineer entry
    - machine learning artificial intelligence research engineer
    - ML AI data bachelors
    - geospatial gis data scientist
    - geospatial gis ML AI
    - data scientist
    - junior data scientist
    - research engineer NLP ML AI
    - generative AI engineer
    - applied scientist
    - data engineer ML AI
    - AI research scientist
    - applied AI research
    - AI strategy innovation
    - Human-AI Interaction
    - computational neuroscience
    - digital health healthcare medtech AI ML data
    - ML AI systems architect
    - ML AI solutions architect
    - urban AI smart cities data
    - knowledge management AI systems
    - knowledge base RAG LLM engineer
    - applied scientist knowledge systems retrieval

# ── DOMAIN PREFERENCES (1 = most preferred) ────────────────

domain_preferences:
  1: Applied ML Research / Research Engineering
  2: NLP & Language ML/ AI
  3: Spatial / Geospatial Data Science
  4: Data Science & Analytics
  5: Generative AI
  6: Computer Vision
  7: ML/AI Engineering / MLOps
  other_open_to:
    - Knowledge Systems / Applied LLM for research & sensemaking (emerging focus — see §2.10)
    - Conversational AI
    - Interdisciplinary AI Research (cognitive science, healthcare AI, climate AI)
    - AI Product Development (research-adjacent)
    - Data Engineering (if ML pipeline-heavy)

# ── INDUSTRY PREFERENCES ───────────────────────────────────

industry_preferences:
  preferred:
    - "HealthTech / MedTech — NLP for clinical notes, medical imaging, brain-computer interface research, health data science; intersects with neuroscience, medicine, and biology interests"
    - "Climate & Sustainability / Environmental Tech — spatial data science for environmental monitoring, climate modelling, biodiversity tracking; connects GIS background and ML skills to meaningful application"
    - "Research / Academia (industry labs) — A*STAR, NUS/NTU research divisions, Sea AI Lab, Grab AI, Google DeepMind Singapore; aligns with Applied Scientist trajectory"
    - "Creative & Cultural Tech — AI for language, music, cultural applications; connects linguistics, arts, and anthropology interests"
  neutral:
    - "GovTech / Public Sector — relevant experience (CIPA, MFCD); capable of navigating government data and stakeholder complexity, though slightly wary of rigid structures and lag in technology adaptation"
    - "Defence / Security — Digital Forensics, Defence AI; technically interesting but domain-neutral"
    - "FinTech — interesting data problems, but personally disengaged with the domain itself; acceptable if AI research quality is high"
  avoid:
    - "Pure FinTech with no research depth (e.g., trading infrastructure, payment ops)"
    - "e-commerce / retail (optimisation-heavy, low research depth)"
  notes: "Will consider any industry if the AI/ML work is research-quality, applied science, or has clear societal / human impact. Knowledge-systems / knowledge-management work is especially appealing wherever it supports research, sensemaking, or decision-making in complex domains."

# ── COMPANY TYPE PREFERENCES ───────────────────────────────

company_preferences:
  core_requirement: "Skillful teams and strong technical infrastructure — an environment where I can learn, grow, and be challenged. Receptive to innovation and adaptation."
  preferred_types:
    - Research institutes and labs (A*STAR, NUS/NTU, independent labs)
    - AI-first or deep-tech startups with serious engineering culture
    - Established tech firms (regional or global) with strong AI/data divisions
    - Government-linked companies (GLCs) with active technology transformation
    - MNCs with dedicated research or applied science teams
  culture_priorities:
    - High learning velocity — will be challenged to grow
    - Collaborative, intellectually curious team
    - Meaningful or research-driven work
    - Openness to initiative and innovation
    - Mentorship or structured growth opportunities
  dealbreakers:
    - "Purely siloed, manual, or maintenance work with no technical growth"
    - "Environment where curiosity and initiative are not valued"
    - "No AI/ML/data in the actual work (only in the company's products)"

# ── SKILL PROFICIENCY REGISTRY ─────────────────────────────

skills:
  # ── Languages ──────────────────────────────────────────
  languages:
    Python:       Expert
    Java:         Expert
    C:            Expert
    Jupyter:      Expert
    VSCode:       Expert
    C_Plus_Plus:  Working
    SQL:          Working
    JavaScript:   Working
    Assembly:     Working
    Vim:          Working
    NoSQL_MongoDB: Familiar
    CSharp:       Familiar

  # ── Machine Learning & AI ──────────────────────────────
  ml_and_ai:
    TensorFlow_Keras:                  Working
    Scikit_Learn:                      Working
    Classification_Models_Algorithms:  Working   # kNN, Decision Trees, AdaBoost, Ensemble Learning
    Model_Optimization:                Working   # Hyperparameter Tuning, Batch Normalisation, LR Scheduling
    SMOTE:                             Working
    Reinforcement_Learning:            Familiar  # Q-Learning, DQN
    Genetic_Algorithms_Evolutionary:   Familiar
    Transfer_Learning:                 Familiar
    OpenAI_Gym:                        Familiar
    PyBullet:                          Familiar

  # ── Generative AI & LLMs ───────────────────────────────
  generative_ai_and_llms:
    GPT2_Finetuning:             Familiar
    Transformers:                Familiar
    VAEs:                        Familiar
    LLM_RAG:                     Familiar
    Vision_Language_Models:      Familiar  # CLIP, GPT-4o
    Agentic_AI_MultiAgent:       Familiar
    MusicVAE:                    Familiar
    Speech_Synthesis_DiffSinger: Familiar
    Latent_Space_Manipulation:   Familiar

  # ── Knowledge Systems & LLM Applications ───────────────
  knowledge_systems:
    LLM_Application_Integration: Working   # Anthropic Claude API — knowledge base + agentic tooling
    Prompt_Engineering:          Working
    Agentic_Pipelines:           Familiar
    RAG_Retrieval:               Familiar
    Knowledge_Base_Design:       Familiar  # Obsidian / Markdown vaults, git-versioned
    Structured_Extraction:       Familiar
    Obsidian:                    Familiar

  # ── Computer Vision ────────────────────────────────────
  computer_vision:
    OpenCV:                           Working
    CNNs:                             Working
    OCR:                              Working
    Object_Detection:                 Working
    Image_Augmentation:               Working   # Albumentations
    Frame_Differencing_BG_Subtraction: Working
    FFmpeg_FFprobe:                    Familiar  # video format validation & transcoding, ISP coursework

  # ── NLP ────────────────────────────────────────────────
  nlp:
    NLTK:                Working
    spaCy:               Working
    TF_IDF:              Working
    Text_Classification: Working
    NER:                 Familiar

  # ── Data Science & Analytics ───────────────────────────
  data_science:
    Pandas:                   Working
    NumPy:                    Working
    Matplotlib_Seaborn:       Working
    EDA:                      Working
    Feature_Engineering:      Working
    Dimensionality_Reduction: Working
    Statistical_Analysis:     Working
    Data_Preprocessing:       Working
    Predictive_Modeling:      Familiar

  # ── Backend & Databases ────────────────────────────────
  backend_and_databases:
    MySQL:                Working
    RDBMS_NoSQL_Design:   Working
    Schema_Normalization: Working   # 3NF, Entity-Relationship modelling
    FastAPI:              Familiar
    NodeJS_Express:       Familiar
    PostgreSQL:           Familiar
    MongoDB:              Familiar
    RESTful_APIs:         Familiar
    Google_Firebase:      Familiar
    Alembic:              Familiar

  # ── DevOps & Tools ─────────────────────────────────────
  devops_and_tools:
    Claude Code: Working
    Git_GitHub:  Working
    Linux_Bash:  Working
    TensorBoard: Working
    Docker:      Familiar
    GCP:         Familiar

  # ── GIS & Geospatial ───────────────────────────────────
  gis_and_geospatial:
    ArcGIS_Pro:              Working
    ArcPy:                   Working
    Geodatabase_Management:  Working
    SVY21_Coordinate_System: Working
    GIS_Submission_Standards: Working  # TOPO, LCDW/TCDW, GPR/MCGPR, TT, CUP/DIR/GeoCUP, data quality grading
    Data_Dictionary_Design:  Familiar  # SG-DRM template, legacy-to-SQL type mapping

  # ── Software Engineering ───────────────────────────────
  software_engineering:
    OOP:                  Working
    Agile_Scrum:          Working
    TDD:                  Working
    Modular_Architecture: Working
    Unit_Testing:         Working
    Sprint_Planning:      Working
    UI_UX_Design:         Working
    Notion:               Working

  currently_learning: # anything actively being picked up
    - PyTorch
    - cloud deployment
    - vector/graph databases
    - retrieval-augmented generation (RAG) & retrieval evaluation
    - knowledge graphs / knowledge representation
    - N8N

# ── APPLICATION LOGISTICS ──────────────────────────────────

application_logistics:
  resume_format: LaTeX (one-page PDF)
  cover_letter_format: Plain text / PDF
  follow_up_format: LinkedIn message or email (Plain text)
  references_available: On request
  reference_contacts: References available upon request
  publications: None currently
  awards_recognition: None currently
  portfolio_website: None currently (in progress)

---

<!-- ========================================================
     NARRATIVE SECTIONS
     Read by AI to generate cover letters, resume bullets,
     and follow-up messages. Written in first person.
     ======================================================== -->


# ALEX TAN — APPLICATION PROFILE


## 1. PROFESSIONAL SUMMARY

Recent Computer Science graduate specialising in Machine Learning and AI, with hands-on experience spanning NLP, computer vision, geospatial data systems, and full-stack, LLM-integrated applications. The through-line in my work is a curiosity about how knowledge and context get encoded into and retrieved by systems — increasingly framed as knowledge systems / knowledge management — alongside a belief that the most interesting problems sit at the intersection of technical systems and human context, whether that's language, place, or behaviour. I'm looking for a role where I can experiment rigorously, go deep on meaningful problems, and grow alongside people who take ideas seriously.

**Tailoring notes:**
- Full version: signals research mindset, interdisciplinary instinct, depth over breadth
- For applied/product-facing roles: trim the last sentence; emphasise hands-on delivery (AeroScope, CIPA)
- For research roles: lead with "research curiosity" framing; reference FYP benchmark result early
- For knowledge-systems / applied-LLM roles: lead with the AeroScope knowledge base and the automation pipeline, framed around retrieval and how knowledge is structured and made queryable


## 2. CAREER NARRATIVE

<!--
  One paragraph per target domain — raw ingredients for personalised
  cover letter introductions. Ordered by domain preference ranking.
-->

### 2.1 Applied ML Research

I'm drawn to research because I find the process of forming a hypothesis and systematically testing it genuinely satisfying — not as an academic exercise, but as a way of understanding something that wasn't understood before. What excites me most is the applied dimension: research that feeds back into real systems or decisions, where curiosity and rigour serve a purpose beyond publication. I want to be at the frontier of what's possible, not just implementing what's already established.


### 2.2 NLP & Language AI

Language is the domain where I feel the deepest personal pull, because it sits at the intersection of the things I find most interesting — cognition, meaning, human behaviour, and the mechanics of how understanding actually works. What excites me about NLP isn't just the technical challenge of processing text, but the underlying question it keeps asking: what does it mean to *understand* something? Working in this space feels like contributing to a problem that is simultaneously computational and deeply philosophical.


### 2.3 Spatial & Geospatial Data Science

There's something compelling about the idea that place encodes information — that where something is tells you something meaningful about what it is and what it might become. My experience at CIPA showed me how geospatial data can directly inform decisions about infrastructure, environment, and urban life, and I'm excited by the potential to apply ML to those problems more rigorously. It also connects naturally to my interest in sustainability and ecology, where the stakes of getting spatial analysis right are genuinely high.


### 2.4 Data Science & Analytics

What draws me to data science is the objectivity of it — the idea that if you ask the right question and structure the data correctly, it will tell you something true. I find the exploratory phase genuinely absorbing: the process of cleaning, interrogating, and visualising a dataset to find patterns that weren't obvious at first. I'm also motivated by the communication side — translating analytical findings into something a non-technical person can act on feels like a real and underrated skill.


### 2.5 Generative AI

Generative systems fascinate me because they're one of the few areas in ML where the output is creative in a way that feels genuinely novel — not classification or prediction, but *making* something. My coursework in music generation, speech synthesis, and fine-tuning language models gave me a taste of that, and I want to go deeper, particularly in multimodal and language-grounded generation. There's also a philosophical dimension I can't ignore: what does it mean for a machine to generate something meaningful, and where does that break down?


### 2.6 Computer Vision

My FYP was built entirely around a CV problem — optimising a CNN classification pipeline for handwritten digit OCR — and it was one of the most technically engaging projects I've done. The iterative process of experimenting with model architectures, augmentation strategies, and understanding *why* certain approaches worked on this particular type of data was genuinely absorbing. At AeroScope, I'm building annotation infrastructure for P&ID technical drawings as training data for downstream CV models, which adds a practical, production-adjacent dimension to that interest.


### 2.7 ML/AI Engineering / MLOps

<!--  Note: drawn to this more as the execution layer for research/NLP interests than as a primary domain. -->

Building robust ML pipelines — from data preprocessing through training, evaluation, and deployment — is the connective tissue that makes research actually usable. At AeroScope, I've had to think about this practically: structuring a backend architecture that supports a future AI roadmap, not just today's feature set. I'm interested in developing more rigour here, particularly around scalable pipelines and production-grade ML systems.


### 2.8 Conversational AI *(include for relevant roles)*

What interests me about conversational systems isn't the chatbot surface — it's the hard problem underneath: how do you build something that understands context, handles ambiguity, and responds in a way that feels coherent across a conversation? That question connects directly to my interest in cognition and what makes human communication distinctive, and I think there's still a lot of genuinely unsolved science in this space, not just engineering.


### 2.9 Interdisciplinary / Cross-Domain Motivation

The thread connecting my technical work and my broader intellectual life is a curiosity about how understanding happens — in machines, in humans, and in the space between them. The ideas in Brian Christian's *The Most Human Human* — about what skills make us distinctly human, and how AI's mode of learning differs from ours — exemplify the kind of interdisciplinary inquiry I find most alive. Through my mentorship with Dr. Mei Lin Goh, I've seen what a research career looks like when cognitive science, healthcare, and AI are genuinely integrated — and that's the direction I want to move toward. I'm particularly drawn to areas like computational linguistics, attention and perception, cognitive-AI intersections, and the ethics and philosophy of intelligent systems.


### 2.10 Knowledge Systems & Knowledge Management *(emerging focus)*

Increasingly, the through-line across my work is a fascination with how knowledge and context get encoded into, structured within, and retrieved from systems — and how much that determines whether a system is actually useful. I've come to see knowledge management not as filing and search, but as the design problem underneath good research tooling, good AI, and good decision-making: how you represent what's known so that both people and models can reason over it well. It's a deliberately cross-functional thread — it travels into any domain — and it's where I most want to build, particularly for research, sensemaking, and AI in complex, high-stakes settings (health being one I keep returning to). This crystallised through building an LLM-backed knowledge base at AeroScope and through my own agentic tooling, and it's now the lens I use to choose what to learn and which problems to pursue.


## 3. TECHNICAL SKILLS WITH CONTEXT

### 3.1 Machine Learning & AI
**Skills:** TensorFlow/Keras, Scikit-Learn, kNN, Decision Trees, AdaBoost, Ensemble Learning, SMOTE, Hyperparameter Tuning, Batch Normalisation, Learning Rate Scheduling

**Context:** Applied across 5+ projects — classification (fake news detection: 98.4% accuracy; handwritten digit OCR: 93.92%), data science pipelines (EUI prediction), and coursework covering RL, evolutionary AI, and multi-agent systems. Most confident in supervised learning pipelines, classification models, and CNN-based image tasks. Reinforcement learning and genetic algorithms applied in coursework; working-level familiarity with concepts and implementation, less so with production deployment.


### 3.2 Generative AI & LLMs
**Skills:** GPT-2 Fine-tuning (Hugging Face), Transformers, VAEs (MusicVAE), RAG, Vision-Language Models (CLIP, GPT-4o), Agentic AI, Speech Synthesis (DiffSinger), Latent Space Manipulation

**Context:** Coursework involved fine-tuning GPT-2 for lyric generation, MusicVAE for MIDI composition, and DiffSinger-inspired speech synthesis — full creative pipeline. At AeroScope, scoping an agentic pipeline using CLIP/GPT-4o for zero-shot inspection comment generation. RAG proposed for LLM-based GIS validation at CIPA. Coursework generative-AI work is at Familiar level; applied LLM-integration work (Claude API, prompt engineering, agentic tooling) is at Working level — see §3.9.


### 3.3 Computer Vision
**Skills:** OpenCV, Albumentations, CNNs, OCR, Object Detection, Image Augmentation, Frame Differencing, Background Subtraction, Morphological Operations, FFmpeg, FFprobe, Konva.js (canvas annotation)

**Context:** FYP built a full CNN OCR pipeline on 90K+ samples, benchmarked against IEEE paper, with custom augmentation pipeline (OpenCV + Albumentations). Traffic monitoring project implemented a real-time classical CV pipeline (frame differencing, contour tracking). Intelligent Signal Processing coursework also covered video/audio signal handling end-to-end: a video format validation and conversion tool using FFprobe (codec/resolution/frame-rate/bitrate inspection) and FFmpeg (automated transcoding to spec), alongside a lossless audio compression implementation (Rice coding). At AeroScope, building annotation tooling for P&ID engineering drawings with geometric overlays persisted as structured JSON for downstream ML training data.


### 3.4 NLP
**Skills:** NLTK, spaCy, TF-IDF, Text Classification, Tokenisation, Lemmatisation, Named Entity Recognition, URL parsing, Source metadata extraction

**Context:** Built a dual-feature fake news classifier using TF-IDF vectorisation + URL source metadata, achieving 98.4% accuracy and AUC 0.983. Familiar with classical NLP preprocessing pipelines end-to-end. Interest in computational linguistics and the deeper question of language understanding drives desire to go further in this area.


### 3.5 Data Science & Analytics
**Skills:** Pandas, NumPy, Matplotlib, Seaborn, EDA, Feature Engineering, Dimensionality Reduction, Statistical Analysis, Data Preprocessing

**Context:** Applied across EUI prediction (linear regression with domain-engineered features — chiller age, solar panel presence, AC efficiency) and wine review analytics (30K+ records, SQL-powered). Comfortable with the full data pipeline: raw ingestion → cleaning → EDA → feature engineering → modelling → visualisation and communication of insights.


### 3.6 Backend & Databases
**Skills:** FastAPI, PostgreSQL (JSONB), MySQL, MongoDB, Node.js, Express.js, Google Firebase, RESTful API Design, Schema Normalisation (3NF), Alembic Migrations

**Context:** At AeroScope, architecting a FastAPI/PostgreSQL backend with JSONB for schema-flexible metadata, Alembic migrations, and a local-to-cloud Docker path. MySQL coursework project designed a 3NF-normalised database for 30K+ records with analytics querying. Node.js/Express used for NimbusTech solar dashboard and wine review platform. Backend skills are Working for MySQL/schema design; Familiar for FastAPI/PostgreSQL/MongoDB (in active use, building depth).


### 3.7 DevOps & Software Engineering
**Skills:** Git/GitHub, Docker, Linux/Bash CLI, Agile/Scrum, TDD, Modular Architecture, Unit Testing, OOP, Sprint Planning, UI/UX Design, Notion

**Context:** Practised Git branching strategies and modular service-layer architecture at AeroScope. Agile/Scrum applied in Voyage mobile app project (Project Manager role — sprint planning, resource allocation, user-centred design). Linux CLI used daily at CIPA and in personal dev environment. Docker and GCP at Familiar level — have used, actively developing depth.


### 3.8 GIS & Geospatial
**Skills:** ArcGIS Pro, ArcPy, Geodatabase Management, SVY21 Coordinate System, Batch Processing, Attribute Scrambling, GIS Submission Standards, Data Dictionary Design, CAD-to-GIS Conversion

**Context:** Built a Python/ArcPy toolbox at CIPA for large-scale geodatabase automation with custom data redaction, batch processing, and error handling. Authored the team Data Management Handbook. Also contributed to GIS Submission Template standards and a data quality grading framework, and set up the SG-DRM data dictionary template, mapping legacy field formats to standard SQL data types. Gained working knowledge of CAD-to-GIS (2D→3D) conversion pipelines through cross-agency coordination on underground utilities infrastructure planning. GIS is a genuine differentiator for spatial AI/data science roles; not a primary career direction, but a meaningful applied capability with real-world government-scale experience.


### 3.9 Knowledge Systems & LLM Applications
**Skills:** LLM integration (Anthropic Claude API), Retrieval-Augmented Generation (RAG), knowledge-base design, agentic pipelines, prompt engineering, structured extraction, Obsidian (Markdown knowledge vaults), Git-versioned document stores

**Context:** Building an LLM-backed knowledge base ("second brain") at AeroScope over a Google Drive + Obsidian vault (git-versioned), queried via Claude, that maps company files to business processes into a queryable system (see §4.1 / §5.3b). Separately, built a self-directed agentic pipeline (Claude API, Python) that generates tailored application materials from a structured profile and scraped job listings, with a feedback loop and cross-listing skills-frequency analysis (see §5.12). Growing depth in retrieval, knowledge representation, and evaluation: RAG/retrieval at Familiar level; prompt-engineering and LLM-application assembly at Working level. This is the capability I'm most actively deepening (see §2.10).


## 4. EXPERIENCE

### 4.1 AeroScope Technologies — Applied AI & Full-Stack (Contract, Stakeholder Projects)
**Period:** April 2026 – Present
**Relevant domains:** Applied AI, AI Product Dev, Knowledge Systems / Applied LLM, Computer Vision, NLP, Full-Stack
**Keywords:** FastAPI, React, PostgreSQL, JSONB, Konva.js, python-docx, Pillow, OpenCV, CLIP, GPT-4o, Agentic AI, Document Generation, Multimodal AI, Training Data Pipeline, Docker, Alembic, LLM Knowledge Base, RAG, Retrieval, Obsidian, Claude, Knowledge Management, Document Intelligence, Second Brain

**STAR Bullets — Project 1: Inspection Report Automation Platform**
- **S/T:** Tasked with replacing a fully manual UAV inspection report workflow for industrial asset inspections (confined space, offshore platforms) with an end-to-end automated platform, architected to support a future ML roadmap rather than just today's feature set.
- **A (built):** Architected and implemented a Python/FastAPI REST backend with a React frontend and PostgreSQL database (JSONB for schema-flexible metadata) and Alembic migrations, on a local-to-cloud path via Docker — with a versioned Pydantic schema as the single source of truth and the data, rendering, annotation, and UI layers kept decoupled.
- **A (built):** Engineered a deterministic document-generation engine (python-docx, Pillow/OpenCV) that assembles reports from stored data via image compositing, template-matched layout, and dynamic table construction — a pure `data → .docx` export where the stored JSON, not the document, is authoritative.
- **A (built):** Built a canvas-based P&ID annotation tool (React/Konva.js) that persists geometric overlays (bounding boxes, directional arrows) as structured, editable JSON specs, with coordinates stored relative to the original full-resolution image — architected as a labelled dataset pipeline for future CV/NLP model training.
- **A (designing):** Scoping — not yet built — an agentic AI roadmap using vision-language models (CLIP, GPT-4o) for zero-shot inspection-comment generation and human-in-the-loop report drafting; the annotation schema above is being designed now to make that training data available later.
- **R:** *(in progress — replace [FILL IN] once measurable)* Automated report assembly targeting a reduction of ~60% time taken for manual reporting; [FILL IN] report types automated and [FILL IN] drawings annotated to date. Delivered end-to-end for an external stakeholder (reference available upon request).

**STAR Bullets — Project 2: AI Knowledge Base / "Second Brain" (from 16 Aug 2026)**
- **S/T:** Engaged to decentralise the company's institutional knowledge — currently siloed with a single administrator/decision-maker — into a queryable system so that work can continue autonomously in their absence.
- **A (building):** Building an LLM-integrated knowledge base ("second brain") for the business — a Google Drive document vault with an Obsidian knowledge layer, git-versioned, queried via Claude — that maps company files to business processes and workflows into a queryable system. Directly connected to enterprise Q&A / document-intelligence and knowledge-management problems.
- **R:** *(in progress)* Aiming to reduce single-administrator dependency and make institutional knowledge retrievable across the team; [FILL IN] once measurable.


### 4.2 Civic Infrastructure Planning Authority (CIPA), Geospatial Planning Division — GIS Intern
**Period:** June 2025 – November 2025
**Relevant domains:** Data Engineering, Spatial Data Science, Applied AI (RAG/LLM proposal)
**Keywords:** ArcPy, ArcGIS Pro, Python, Geodatabase, Attribute Scrambling, Batch Processing, RAG, LLM, Data Quality, UAT, Government Platform, Technical Communication, GIS Submission Standards, Data Dictionary Design, SG-DRM, CAD-to-GIS Conversion, Geometric Transformation, 3D Modeling, CAD, Underground Utilities Infrastructure, Cross-Agency Coordination

**STAR Bullets:**
- **S/T:** Required to automate extraction of sensitive UAT (User Acceptance Testing) datasets from large-scale national geodatabases for the GeoLink Whole-of-Government platform, while preserving schema integrity and redacting sensitive utility data.
- **A:** Developed a Python/ArcPy ArcGIS Pro Toolbox implementing custom attribute-scrambling logic (itertools), comprehensive error handling, multi-value batch processing, and environment management (workspace restoration, overwrite protection) to ensure reliability across large-scale datasets
- **A:** Proposed a RAG/LLM-based automated validation pipeline for GIS submissions; authored the team's Data Management Handbook covering ArcPy, GIS fundamentals, and data quality frameworks for underground utility planning.
- **A:** Co-developed GIS Submission Template standards and a data quality grading framework (Grade A–E) used to assess submissions from Lead Implementing Agencies and contractors.
- **A:** Set up the SG-DRM data dictionary template, mapping legacy field formats to standard SQL data types across submission datasets.
- **A:** Built cross-agency domain knowledge of Singapore's underground utilities infrastructure planning ecosystem through induction and coordination meetings, and assisted in CAD-to-GIS (2D→3D) conversion workflows.
- **A:** Served as technical liaison during UAT for the GeoLink platform, translating software architecture and security concepts for senior engineering leadership.
- **R:** Reduced UAT data extraction time by 80%, data formatting and handbook adopted by team


### 4.3 Ministry of Family & Community Development (MFCD), Community Social Work Division — Project Coordinator
**Period:** August 2021 – December 2021
**Relevant domains:** Cross-functional coordination, public sector, stakeholder communication
**Keywords:** Agency coordination, Infographics, Reporting, Excel Macros, Social Policy, Communication, Initiative Design

**STAR Bullets:**
- **S/T:** Coordinated cross-agency initiatives to enhance casework skills for social work undergraduates under the Community Social Work Division.
- **A:** Designed infographics, newsletters, and reports to communicate key social welfare insights to internal and external stakeholders. Streamlined quarterly reporting processes using Excel Macros.
- **A:** Coordinated *Project Compass* and related initiatives, liaising between government agencies and social service sector leaders.
- **R:** Reduced reporting time by 20%

**Tailoring note:** Include for roles requiring cross-functional coordination, public sector experience, or social impact framing. Deprioritise for pure technical roles.


### 4.4 NimbusTech Pte Ltd — Software Engineering Intern
**Period:** March 2019 – July 2019
**Relevant domains:** Full-Stack, Backend, Data Engineering (lightweight)
**Keywords:** Node.js, Express, MongoDB, RESTful APIs, Real-time Data, Dashboard, Solar Analytics

**STAR Bullets:**
- **S/T:** Built a real-time analytics dashboard for solar panel energy consumption monitoring.
- **A:** Developed a Node.js/Express backend with MongoDB, implementing RESTful APIs for live energy data ingestion and a frontend interface for real-time visualisation.
- **R:** None


## 5. PROJECTS

### 5.1 ★ Handwritten Digit Recognition (OCR) — FYP
**Domain tags:** Computer Vision, Deep Learning, Applied ML Research
**Keywords:** CNN, OCR, TensorFlow, Keras, OpenCV, Albumentations, Transfer Learning (VGG16), RNN, LSTM, TensorBoard, Batch Normalisation, Learning Rate Scheduling, Data Augmentation, Image Classification
**GitHub:** https://github.com/alex-tan-demo/handwritten-digit-recognition-demo
**Metrics:** 93.92% accuracy — surpassed 93.16% IEEE benchmark on 90,000+ samples
**Summary:** Optimised a CNN image classification pipeline for offline handwritten digit OCR. Designed a custom data augmentation pipeline (OpenCV + Albumentations), benchmarked CNNs, RNNs, LSTMs, and transfer learning (VGG16) to identify drivers of performance on high within-class variance character data. Tracked all experiments with TensorBoard.
**Best fit for:** Computer vision, OCR/document intelligence, applied ML research, deep learning engineering


### 5.2 ★ News Source Credibility Classifier
**Domain tags:** NLP, Machine Learning, Data Science
**Keywords:** AdaBoost, Decision Trees, TF-IDF, spaCy, NLTK, SMOTE, Text Classification, Feature Engineering, Source Metadata, Binary Classification, AUC
**GitHub:** https://github.com/alex-tan-demo/news-credibility-classifier-demo
**Metrics:** 98.4% accuracy, AUC 0.983, 98.1% recall on 2,046 articles — surpassed prior benchmark
**Summary:** Built a dual-feature text classifier combining TF-IDF vectorisation with URL-based source metadata to detect fake news. Full NLP preprocessing pipeline (tokenisation, lemmatisation, URL parsing with spaCy and NLTK). Applied SMOTE for class imbalance. The dual-feature approach (content + source) was the key differentiator over single-feature prior work.
**Best fit for:** NLP, ML engineering, data science, trust & safety, information quality, media/journalism tech


### 5.3 AeroScope Inspection Report Automation Platform
**Domain tags:** Applied AI, AI Product Dev, Computer Vision, NLP, Agentic AI, Full-Stack
**Keywords:** FastAPI, React, PostgreSQL, JSONB, Konva.js, python-docx, Pillow, OpenCV, CLIP, GPT-4o, Docker, Alembic, Multimodal AI, Training Data Pipeline, Agentic AI
**GitHub:** Private/in development — writeup or partial repo available on request
**Metrics:** In progress — projected report-assembly time reduced by ~60%; [FILL IN] report types automated, [FILL IN] drawings annotated (replace once measurable)
**Summary:** End-to-end report automation platform for UAV/drone industrial inspections, replacing a fully manual Word-document assembly workflow, delivered for an external stakeholder. **Built:** a decoupled FastAPI/PostgreSQL (JSONB) backend with a versioned Pydantic schema as single source of truth; a deterministic `data → .docx` generation engine (python-docx, Pillow/OpenCV) with image compositing and dynamic tables; and a React/Konva.js annotation tool that persists P&ID overlays as editable JSON specs (coordinates relative to full-res source), architected as a labelled dataset pipeline for downstream CV/NLP training. **Designing (not yet built):** an agentic pipeline using vision-language models (CLIP, GPT-4o) for zero-shot inspection-comment generation with human-in-the-loop review.
**Best fit for:** Applied AI / AI product engineering, full-stack with AI focus, data-centric ML infrastructure, computer vision (annotation/data pipeline)
**Tailoring note:** For research / applied-scientist roles, lead with the FYP (handwritten digit OCR — benchmark result) as the flagship and let AeroScope support it; for AI-product / full-stack / applied-AI-engineering roles, lead with AeroScope (this platform + the knowledge base, §5.3b) and let the FYP support.


### 5.3b AeroScope AI Knowledge Base — "Second Brain"
**Domain tags:** Applied AI, Knowledge Systems, LLM/RAG, Knowledge Management, Agentic AI, Enterprise Q&A
**Keywords:** LLM, Claude, RAG, Retrieval, Obsidian, Markdown Vault, Google Drive, Git-versioned, Knowledge Base, Document Intelligence, Queryable Knowledge System, Workflow Modelling, Knowledge Representation, Second Brain
**GitHub:** Private/in development — writeup available on request
**Metrics:** In progress (started 16 Aug 2026)
**Summary:** An LLM-integrated knowledge base ("second brain") for the business that turns scattered company files into a queryable system mapped to business processes and workflows. Storage is a Google Drive document vault with an Obsidian knowledge layer, git-versioned; retrieval and querying via Claude. The goal is to decentralise institutional knowledge — currently concentrated in a single administrator/decision-maker — so operations can run more autonomously in their absence. Directly connects to enterprise Q&A, document-intelligence, and knowledge-management problems, and is the applied anchor for my knowledge-systems focus (§2.10).
**Best fit for:** Knowledge systems / applied LLM, RAG & retrieval, enterprise GenAI, document intelligence, knowledge management


### 5.4 ★ CIPA GIS Toolbox — UAT Dataset Automation
**Domain tags:** Data Engineering, Spatial Data Science, Applied AI (RAG/LLM proposal)
**Keywords:** Python, ArcPy, ArcGIS Pro, Geodatabase, Batch Processing, Data Quality, RAG, LLM, Attribute Scrambling, Error Handling, Schema Integrity
**Metrics:** Scripted and tested capability of processing multiple geodatabases, reduced extraction time by 80%
**Summary:** Python/ArcPy toolbox automating UAT dataset extraction from national-scale geodatabases with custom attribute-scrambling for sensitive data redaction, multi-value batch processing, and environment management. Also proposed a RAG/LLM automated validation pipeline for GIS submissions and authored a team Data Management Handbook covering ArcPy, GIS fundamentals, and data quality frameworks. Additionally contributed to GIS Submission Template standards and data quality grading criteria, and set up the SG-DRM data dictionary template (legacy-to-SQL field type mapping) used across submission datasets.
**Best fit for:** Data engineering, spatial data science, GovTech / public sector AI, applied AI to geospatial problems


### 5.5 Building Energy Use Prediction
**Domain tags:** Data Science, Sustainability, Predictive Modelling
**Keywords:** Scikit-Learn, Pandas, Seaborn, Linear Regression, EDA, Feature Engineering, Domain Knowledge, Sustainability, Built Environment
**GitHub:** https://github.com/alex-tan-demo/energy-use-prediction-demo
**Metrics:** Provided a valuable initial study of the data with Exploratory Data Analysis - revealing potential relationships and distributions, Implemented research/domain-based data quality improvements enabling clearer, more meaningful visualisations of the dataset
**Summary:** Developed a linear regression model to predict building energy use intensity from physical and operational characteristics. Conducted EDA and engineered domain-specific features (chiller age, solar panel presence, AC efficiency) to surface actionable insights for energy efficiency optimisation.
**Best fit for:** Data science, sustainability/climate tech, built environment, feature engineering focus


### 5.6 Automated Traffic Monitoring & Counting System
**Domain tags:** Computer Vision, Signal Processing, Smart City
**Keywords:** Python, OpenCV, Frame Differencing, Background Subtraction, Morphological Operations, Vehicle Detection, Urban Planning, Real-time CV
**Metrics:** ~80% accuracy for urban traffic flow vehicle counting
**Summary:** Computer vision pipeline for real-time vehicle detection and counting using classical CV techniques (frame differencing, background subtraction, morphological operations, contour tracking). Applicable to smart city, urban planning, and infrastructure monitoring.
**Best fit for:** CV, signal processing, smart city/urban tech, classical CV pipelines


### 5.6b Automated Video Format Validation & Conversion Tool
**Domain tags:** Computer Vision, Signal Processing, Media Processing, Automation
**Keywords:** Python, FFmpeg, FFprobe, Video Transcoding, Codec Validation, Jupyter, Batch Processing
**Summary:** Built a Jupyter/Python application for a digital film festival's submission pipeline that uses FFprobe to inspect codec, resolution, frame rate, aspect ratio, and bitrate metadata for submitted films, flags non-compliant files with an auto-generated report, and automatically transcodes flagged videos to the required spec (MP4 container, H.264 video, AAC audio) using FFmpeg.
**Best fit for:** Computer vision/media pipelines, signal processing, automation-heavy data engineering roles


### 5.7 Multi-Agent Scientific Discovery System
**Domain tags:** AI Research, Multi-Agent Systems, Knowledge Representation
**Keywords:** Multi-agent architecture, Knowledge representation, Experiment design, Scientific reasoning, Hypothesis generation, Automated discovery
**Metrics:** None
**Summary:** Developed knowledge representation models for scientific domains and a multi-agent architecture for collaborative automated experiment design and hypothesis generation. Explored scientific reasoning algorithms for systematic hypothesis testing.
**Best fit for:** AI research, research engineering, automated science, multi-agent systems, knowledge representation


### 5.8 AI Music Generation System
**Domain tags:** Generative AI, Creative AI, Multimodal Generation
**Keywords:** GPT-2, Hugging Face Transformers, MusicVAE, Latent Space Manipulation, MIDI Generation, Speech Synthesis, DiffSinger, Computational Creativity, End-to-End Pipeline
**Summary:** Integrated generative pipeline for AI-generated song creation: GPT-2 fine-tuned for lyric generation, MusicVAE for MIDI music composition, and DiffSinger-inspired speech synthesis for vocal generation. Evaluated using established computational creativity metrics.
**Best fit for:** Generative AI, creative tech, AI research (creativity, multimodal)


### 5.9 Evolving Virtual Creatures System
**Domain tags:** AI Research, Evolutionary / Bio-Inspired AI, Simulation
**Keywords:** Genetic Algorithms, PyBullet, URDF, Physics Simulation, Fitness Functions, Morphology Design, Evolutionary Encoding, Emergent Design
**Summary:** Genetic algorithm framework for evolving 3D robot morphologies in physics simulation (PyBullet). Designed novel genetic encoding schemes and fitness functions to evaluate morphological performance across generations. Analysed evolutionary trends and emergent design patterns.
**Best fit for:** AI research, evolutionary/bio-inspired computing, robotics (adjacent), simulation


### 5.10 Interactive Wine Review Data Platform
**Domain tags:** Data Engineering, Backend, Database Design
**Keywords:** MySQL, Node.js, Express.js, Mustache.js, Database Normalisation, 3NF, Entity-Relationship Modelling, SQL Queries, Web Application, Large Dataset Analytics
**Summary:** Normalised MySQL database for 30,000+ wine reviews applying 3NF and ER modelling, paired with a dynamic Node.js/Express web application for interactive analytics. Engineered SQL queries for complex analytical retrieval and optimised for large-dataset performance.
**Best fit for:** Data engineering, backend, database-heavy, full-stack roles


### 5.11 Voyage — Cross-Platform Carpooling Application
**Domain tags:** Full-Stack, Mobile, Agile Project Management
**Keywords:** C#, Xamarin Forms, Google Firebase, Agile/Scrum, UI/UX Design, Git, Sprint Planning, Cross-Platform Mobile, User-Centred Design
**Summary:** Led a 4-person team as Project Manager and Product Developer. Delivered a carpooling mobile app for Singapore's transport market with authentication, real-time chat, search, and Firebase integration using Agile/Scrum. 85% feature completion with iterative user-centred prototyping.
**Best fit for:** Roles requiring project leadership, mobile/full-stack, agile PM experience, product development


### 5.12 Automated Job Application System
**Domain tags:** Applied AI, Agentic AI, LLM Systems, Automation, Knowledge/Retrieval
**Keywords:** Anthropic Claude API, Python, LaTeX, Google Sheets, GitHub, Prompt Engineering, Prompt Caching, Structured Extraction, Agentic Pipeline, Skills-Frequency Analysis, Feedback Loop, Voice/Style Control
**GitHub:** In progress (generated-docs repo: github.com/alex-tan-demo/job-app-docs)
**Metrics:** None currently
**Summary:** Self-directed agentic pipeline (Claude API, Python) that generates tailored resumes (LaTeX), cover letters, application-question answers, and outreach from a single structured career profile plus a scraped job listing, with a feedback loop that folds edits back in. Uses Google Sheets as the listings/status datastore (extraction, document-generation status tags, per-row instructions) and GitHub to store generated documents. Curates required skills across listings by frequency and maps them to an interest rating to guide skill-building. A recent iteration added a shared voice specification so every generated document matches my writing style.
**Best fit for:** Applied AI, LLM/agent engineering, AI product, automation, knowledge/retrieval tooling


## 6. EDUCATION

**Degree:** BSc Computer Science, AI/ML Specialisation — Second Class Honours (Upper Division)
**Institution:** Ashcroft University London (via Meridian Global Education, Singapore)
**Relevant Coursework:** Machine Learning & Neural Networks, Natural Language Processing, Artificial Intelligence, Intelligent Signal Processing, Data Science, Databases & Advanced Data Techniques, Algorithms & Data Structures, Computer Security, Software Design & Development, Agile Software Projects

**Notable academic result:** Final Year Project surpassed IEEE benchmark — Handwritten digit OCR at 93.92% vs 93.16% benchmark on 90,000+ samples.

**Certifications / Additional Courses:**
None (as of June 2026)

**Awards / Academic Recognition:** None currently


## 7. LEADERSHIP & EXTRACURRICULARS

### 7.1 Vice President, Public Relations — Singapore Tamil Youth Toastmasters' Club
**Period:** June 2021 – June 2022
**Highlights:** Led marketing and outreach for Singapore's first youth-led bilingual Toastmasters club. Managed social media, promotional materials, and meeting communications. Secured guest speakers and sponsorship partnerships for the club charter. Implemented a buddy system to improve member retention and participation.
**Skills demonstrated:** Public communication, stakeholder engagement, event coordination, bilingual outreach, team leadership


### 7.2 WITCircle Women Mentoring Programme — Mentee
**Organisation:** SCS-WIT (Singapore Computer Society — Women in Tech), vLookUp
**Period:** May 2025 – Present
**Mentor:** Dr. Mei Lin Goh — Principal Scientist, Machine Intelligence Division, Healthcare & MedTech Research, a Singapore public research institute; background spanning leading research universities, hospitals, and the MedTech sector.

**What I gained:**

*Research landscape in Singapore:* Developed a grounded understanding of how applied research differs from academic research in Singapore's ecosystem — the range of institutions (A*STAR, NUS/NTU labs, independent labs, GLCs), types of research approaches (experimental vs. theoretical, life sciences vs. computational), and access points for early-career researchers.

*Career direction:* The mentorship helped me recognise that applied research — rather than pure engineering or pure academia — is where I want to be. I am intrinsically process-oriented and extrinsically motivated by people-facing, usability-centred application, which complements T-shaped capabilities: broader intellectual range combined with technical depth and analytical rigour. I was encouraged to think beyond the limitations of my background and follow my curiosities, then develop aligned knowledge and skills.

*Action and outcome:* Instigated deeper reflection on my domains of interest, their interdisciplinary potential, and the design of my career trajectory. Led to targeted exploration of aligned roles, research replication projects, and evaluation frameworks. Clarified that the intersection of AI, cognitive science, language, and human-centred systems is where I want to build — and, more recently, sharpened into a focus on knowledge systems / knowledge management (see §2.10).

**Cover letter framing:** *"Through the WITCircle mentorship programme, I gained direct insight into how ML research is applied within Singapore's tech ecosystem, which affirmed my interest in roles at the boundary of research and real-world impact."*

**Skills demonstrated:** Career intentionality, self-directed growth, professional networking, interdisciplinary thinking, initiative


### 7.3 Other Involvement
  - Part-time Mathematics, Biology/Chemistry tutor
  - SINDA (Singapore Indian Association) Volunteer Work
  - Professional Classical Dancer
  - Crochet/ Arts & Crafts Enthusiast

## 8. SOFT SKILLS & WORKING STYLE

**How I work:**
- Collaborative and team-oriented — I do my best work in an environment where ideas can be shared and built on together
- Design and planning-first — I naturally gravitate toward scoping, structuring, and thinking through architecture before implementation
- Research and curiosity-driven — I approach problems by investigating multiple approaches and trying to understand *why* something works, not just *that* it works
- Detail-oriented and organised — I care about clean structure in data, code, documentation, and communication
- Strong communicator across technical and non-technical contexts — demonstrated at CIPA translating software architecture and security concepts for senior engineering leadership, and at MFCD communicating social policy insights through infographics and reports
- Process-oriented with a people-facing application focus — I find the most satisfaction when technical rigour leads to something that is genuinely useful to someone

**Problem-solving style:** I prefer open-ended, purpose-oriented challenges over well-defined closed problems. I enjoy breaking large problems into components, reasoning through them methodically, and validating solutions across varied edge cases.

**Learning style:** I am a thorough learner — I build understanding before I move forward, and once I know something well, I can teach it and apply it creatively. I am slower to pick up new technical tools but have strong conceptual foundations that accelerate transfer to new domains.

**Areas actively strengthening — beyond frameworks and deployment:**
- **Knowledge systems & retrieval** — how knowledge and context are represented, structured, and retrieved so people and models can reason over them; RAG, knowledge bases, knowledge representation (my current primary focus — see §2.10)
- **Statistical and scientific rigour** — going beyond model accuracy to understand *why* something works: causal inference, experimental design, uncertainty quantification
- **Research methodology** — reading and critiquing papers; forming and testing hypotheses systematically; knowing when a result is actually meaningful
- **Domain expertise** — going deep in a field (NLP, geospatial, healthcare AI) rather than staying a generalist; building a *perspective*, not just skills
- **Technical communication** — turning complex findings into clear writing, visualisations, and briefings for non-technical stakeholders
- **Collaborative and cross-functional research** — working across engineering, domain experts, and product teams
- **Responsible and ethical AI** — bias, fairness, transparency, and societal impact of models; connects to interests in philosophy, ethics, and human behaviour

> *"Beyond technical frameworks, I'm looking to develop more rigorous scientific thinking — learning to design experiments well, interrogate results honestly, and communicate findings clearly across disciplines. I'm also drawn to building deeper domain expertise, particularly at the intersection of language, natural systems, data, and human behaviour — and, increasingly, in how knowledge itself is structured and made retrievable by systems."*


## 9. INTERESTS & INTELLECTUAL CURIOSITY

**Technical / Research interests:**
- Knowledge Systems, Knowledge Management, Knowledge Representation & Retrieval (RAG, knowledge bases, queryable knowledge systems)
- Large Language Models, Attention Mechanisms, Transformer architectures
- Computational Linguistics, Language Understanding, Semantics
- Generative AI — creative and scientific applications, multimodal generation
- Agentic AI and autonomous systems
- Pattern Recognition and Perceptual Learning
- Genetic Algorithms and Bio-inspired Computing
- Responsible AI, Bias & Fairness, AI Ethics
- Blockchain Technology and decentralised systems

**Interdisciplinary interests:**
- Neuroscience, Cognitive Science, Philosophy of Mind
- Psychology and Human Behaviour
- Linguistics and Natural Language
- Biology, Evolution, Life Sciences
- Ethics and Philosophy of Technology
- Mythology, Anthropology, Conservation, Arts and Culture
- Geology, Ecology, Sustainability

**Books / Ideas that have shaped my thinking:**
- *The Most Human Human* — Brian Christian: the intersection of AI capability and what makes human cognition distinctive; the philosophical implications of language and context
- *Thank You for Being Late* - Thomas L. Friedman: An Optimist's Guide to Thriving in the Age of Accelerations
- *My Stroke of Insight* - Jill Bolte Taylor: A Brain Scientist's Personal Journey

**Communities / Conversations drawn to:**
[FILL IN when ready — e.g., NLP research, AI safety, cognitive science, generative art, open-source ML, neuroscience forums — wherever intellectual energy actually goes]

## 10. JOB SELECTION CRITERIA

**Most drawn to roles that offer:**
1. Substantive research or applied science work — not just tooling or maintenance, but forming hypotheses and understanding systems
2. Learning velocity — will be challenged to grow technically and intellectually
3. Meaningful application — work that connects to a real problem, human need, or societal impact
4. Collaborative, intellectually curious team — good people to work with and learn from
5. Domain depth — opportunity to build genuine expertise in NLP, spatial AI, health data, knowledge systems, or a related field
6. Research or innovation culture — curiosity is valued, not just execution

**Signals that make a listing more appealing:**
- Role title includes: Research Engineer, Applied Scientist, NLP Engineer, Data Scientist, ML Engineer, Spatial Data Scientist, Computer Vision Engineer, Knowledge / AI Engineer
- Job description references: research, experimentation, model development, pipeline design, cross-functional collaboration, applied science, knowledge bases / retrieval / RAG
- Company is known for strong engineering or research culture
- Exposure to production systems, research processes, or domains I haven't encountered yet
- Mention of interdisciplinary application (health, environment, language, culture)

**Signals that make a listing less appealing:**
- Primarily maintenance, support, or reporting with no model development
- No mention of AI/ML/data in the actual work (only in the company's products)
- Rigid, bureaucratic environment with no room for initiative
- Pure sales, customer-facing, or non-technical roles

**Weighing factors when choosing between offers:**
Team > Growth > Mission > Domain > Salary

## 11. ADDITIONAL CONTEXT

**Career context (for cover letters):**
Recently completed my Computer Science degree and am actively transitioning into my first full-time role. Since graduating I have taken a GIS data-engineering internship at CIPA and am currently engaged in contract project work with AeroScope — building an AI-integrated inspection-report platform and, more recently, an LLM knowledge base ("second brain") for the business. I am a Singapore citizen available immediately.

**What I want every application to reflect:**
- Genuine research curiosity and intellectual depth — not just technical competence
- The interdisciplinary angle: that my interests in cognition, language, and human systems are not separate from my technical work, but the *reason* for it
- The knowledge-systems thread: an emerging focus on how knowledge and context are encoded into and retrieved by systems, as the cross-functional direction I'm building toward (see §2.10)
- The FYP benchmark result (93.92% vs 93.16% IEEE) as evidence that I engage seriously with the literature and push for rigour
- The WITCircle mentorship as evidence of intentionality and professional self-awareness
- That I'm looking for depth, not just a job title

**Anything to avoid in applications:**
- Overly generic enthusiasm ("passionate about AI and innovation") without specificity
- Framing that implies I'm a generalist without direction — the narrative should have a clear thread
- Underselling the interdisciplinary angle; it is a genuine differentiator, not a soft qualifier

**Publications / Conference presentations / Open-source contributions:** None currently

**Portfolio / Personal website:** None (in progress)
