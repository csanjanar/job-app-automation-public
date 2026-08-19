---
# ============================================================
# JOHN DOE — CONSOLIDATED APPLICATION PROFILE
# Source of truth for job suitability assessment and
# generating tailored resumes, cover letters, and messages.
#
# THIS IS A MINIMAL TEMPLATE, not a real profile. Every section
# below is a fictional placeholder with just 1-2 sample entries —
# enough to show the shape of what goes where. Replace each
# section with your own real information; add as many entries
# as you need (the real thing can run to hundreds of lines).
#
# HOW TO USE:
#   • Fill in every field below with your own details.
#   • Proficiency scale:
#     Expert   = Can lead, teach, and solve complex problems independently
#     Working  = Can build and debug independently
#     Familiar = Have used; comfortable with basics
# ============================================================

profile:
  name: John Doe
  email: john.doe@example.com
  phone: "+65 8123 4567"
  linkedin: linkedin.com/in/johndoe
  github: github.com/johndoe
  location: Singapore
  work_authorisation: Citizen / Permanent Resident (edit to your own status)
  availability: Immediately
  languages_spoken:
    - English (fluent)

# ── JOB SEARCH FILTERS ─────────────────────────────────────

search_filters:
  employment_type:
    - Full-time
  location:
    - Singapore (Hybrid)
  salary_floor_sgd_monthly: 4000
  salary_note: "Open to negotiation depending on role scope"
  experience_level: Entry-level / Fresh graduate
  recency_priority: true   # Only listings posted within last N days AND closing date in the future
  keywords_to_exclude:
    - Sales Engineer
  title_prefixes_to_exclude:   # Skip any listing whose title starts with or contains these
    - Senior

# ── SEARCH TARGETING ───────────────────────────────────────
# Consumed by tools/search_mcf.py (queries + filters) so search behaviour
# lives here with every other preference — not hardcoded in a tool.

search_targeting:
  max_years_experience: 1
  recency_days: 5
  target_count: 5
  excluded_title_words: [senior, lead, manager, director]
  excluded_title_substrings:
    - "(phd)"
  mcf_queries:
    - data analyst entry level
    - junior software engineer

# ── DOMAIN PREFERENCES (1 = most preferred) ────────────────

domain_preferences:
  1: Data Analytics
  2: Software Engineering
  other_open_to:
    - Product Management

# ── INDUSTRY PREFERENCES ───────────────────────────────────

industry_preferences:
  preferred:
    - "Technology — general software/data roles"
  neutral:
    - "Finance — acceptable if the day-to-day work is technical"
  avoid:
    - "Roles with no technical component"
  notes: "Open to most industries as long as the work itself is technical and growth-oriented."

# ── COMPANY TYPE PREFERENCES ───────────────────────────────

company_preferences:
  core_requirement: "A team where I can learn, grow, and be challenged."
  preferred_types:
    - Startups
    - Established tech companies
  culture_priorities:
    - Collaborative team
    - Mentorship available
  dealbreakers:
    - "No room for technical growth"

# ── SKILL PROFICIENCY REGISTRY ─────────────────────────────

skills:
  languages:
    Python: Working
    SQL: Familiar

  data_science:
    Pandas: Working

  devops_and_tools:
    Git_GitHub: Working

  currently_learning:
    - Cloud deployment basics

# ── APPLICATION LOGISTICS ──────────────────────────────────

application_logistics:
  resume_format: PDF (one page)
  cover_letter_format: Plain text / PDF
  follow_up_format: Email
  references_available: On request
  reference_contacts: References available upon request
  publications: None currently
  awards_recognition: None currently
  portfolio_website: None currently

---

<!-- ========================================================
     NARRATIVE SECTIONS
     Read by AI to generate cover letters, resume bullets,
     and follow-up messages. Written in first person.
     Each section below has just 1-2 sample entries — add
     more of your own in the same shape.
     ======================================================== -->


# JOHN DOE — APPLICATION PROFILE


## 1. PROFESSIONAL SUMMARY

Recent graduate in Computer Science, looking for an entry-level role where I can apply my software engineering and data skills and keep learning from a strong team. *(Replace with your own 2-4 sentence summary — this is what generated cover letters open with.)*


## 2. CAREER NARRATIVE

<!--
  One short paragraph per target domain — raw ingredients for personalised
  cover letter introductions. Add one section per domain you're targeting.
-->

### 2.1 Data Analytics

I enjoy the process of turning a messy dataset into a clear, defensible answer to a real question. I'm looking for a role where I can build that skill on real business problems, not just coursework.

### 2.2 Software Engineering

I like building things that work reliably end-to-end — from the data model to the interface. I want a team that will push me to write cleaner, more maintainable code.


## 3. TECHNICAL SKILLS WITH CONTEXT

### 3.1 Data Analysis

**Skills:** Python, Pandas, SQL
**Context:** Used across coursework and one personal project to clean, explore, and visualise datasets. *(Replace with your own skill categories and where you've actually applied them.)*


## 4. EXPERIENCE

### 4.1 Example Company — Software Engineering Intern
**Period:** Jan 2026 – Jun 2026
**Relevant domains:** Software Engineering
**Keywords:** Python, SQL, REST APIs

**STAR Bullets:**
- **S/T:** Tasked with automating a manual weekly reporting process.
- **A:** Built a Python script that pulled data from an internal API and generated a formatted report, replacing a manual spreadsheet process.
- **R:** Reduced report preparation time from 3 hours to 15 minutes.

*(Add one section like this per job/internship, most recent first.)*


## 5. PROJECTS

### 5.1 Example Project — Personal Budget Tracker
**Domain tags:** Software Engineering, Data
**Keywords:** Python, SQLite, CLI
**GitHub:** https://github.com/johndoe/example-project
**Metrics:** N/A
**Summary:** A command-line tool that logs expenses to a local database and generates a monthly spending summary.
**Best fit for:** Software engineering, backend-leaning roles

*(Add one section like this per project. Real profiles typically list 3-10.)*


## 6. EDUCATION

**Degree:** BSc Computer Science
**Institution:** Example University
**Relevant Coursework:** Data Structures & Algorithms, Databases, Machine Learning
**Notable academic result:** *(e.g. a thesis result, a grade, an award — optional)*


## 7. LEADERSHIP & EXTRACURRICULARS

### 7.1 Member — Example University Coding Club
**Period:** 2023 – 2025
**Highlights:** Helped organise a beginner hackathon for first-year students.
**Skills demonstrated:** Event coordination, teamwork

*(Add more entries as relevant — one per role/organisation.)*


## 8. SOFT SKILLS & WORKING STYLE

**How I work:**
- Collaborative — I do my best work talking ideas through with a team
- Detail-oriented — I care about clean, well-documented code

**Problem-solving style:** I like breaking a large problem into smaller pieces and testing my assumptions as I go.


## 9. INTERESTS & INTELLECTUAL CURIOSITY

**Technical / Research interests:**
- Data engineering, applied machine learning

**Communities / Conversations drawn to:**
[FILL IN — e.g. open-source, a specific research area, a hobby community]


## 10. JOB SELECTION CRITERIA

**Most drawn to roles that offer:**
1. Learning velocity — a team that will challenge me to grow
2. Meaningful, technical day-to-day work

**Signals that make a listing less appealing:**
- No technical component to the actual work
- Fully remote with no team collaboration (if that matters to you)

**Weighing factors when choosing between offers:**
Team > Growth > Salary


## 11. ADDITIONAL CONTEXT

**Career context (for cover letters):**
Recently graduated and actively looking for my first full-time role. *(1-2 sentences of real context — visa status, notice period, anything a cover letter needs to reference.)*

**What I want every application to reflect:**
- [Your differentiator — the one thing you want every doc to convey]

**Anything to avoid in applications:**
- Generic phrases like "passionate about technology" with no specifics
