# VLearn Tutor AI — Design Documentation Index

Welcome! This folder contains comprehensive documentation on the AI decision-making architecture, including prompt design, conditional logic, error handling, and safety mechanisms.

---

## 📚 Documentation Suite (5 Files)

### 🚀 Start Here

**[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** (3 pages)
- One-page decision flowchart
- Confidence score reference
- Intent routing table
- Debugging checklist
- Common issues & fixes
- **Best for**: Everyone, especially quick lookups

---

### 🏗️ Complete Architecture

**[PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md)** (20 pages)
- §1: Prompt engineering architecture
- §2: Conditional decision logic (intent routing, context resolution, evidence gathering)
- §3: Error scenarios & safety rules (7 categories)
- §4: Testing & validation strategy
- **Best for**: ML engineers, prompt designers, understanding "why"

**[DECISION_FLOWCHART.md](DECISION_FLOWCHART.md)** (15 pages)
- 8 detailed ASCII flowcharts with annotations
- State machines for routing, context resolution, answer composition
- Provider fallback chains
- Confidence score calculation
- End-to-end example flows
- **Best for**: Developers, visual learners, understanding flows

---

### 🧪 Testing & Validation

**[ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md)** (25 pages)
- §1-2: Error scenarios & safety test cases (8 major categories)
- §3: Confidence calibration tests
- §4-6: Edge cases, failure recovery, performance tests
- §7: Validation checklist (pre-release & post-launch)
- **Best for**: QA engineers, test writers, validation

---

### 🧭 Navigation Guide

**[DESIGN_SUMMARY.md](DESIGN_SUMMARY.md)** (10 pages)
- Quick navigation by role
- Core architecture summary
- Key design decisions explained
- Code locations by topic
- Common modifications guide
- Q&A debugging guide
- **Best for**: Finding what you need quickly

---

## 🎯 Quick Start by Role

### 👨‍💻 **I'm a Developer**
1. Read: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (5 min)
2. Study: [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) §1-3 (15 min)
3. Explore: [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) §2 (20 min)
4. Reference: Keep [QUICK_REFERENCE.md](QUICK_REFERENCE.md) open while coding

### 👨‍🔬 **I'm a Prompt Engineer**
1. Read: [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) §1 (10 min)
2. Check: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) §4 — Safety Rules (5 min)
3. Validate: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) §2 — Safety Tests (10 min)
4. Iterate: Run `python eval/run_eval.py` to verify golden set score ≥85%

### 🧪 **I'm a QA/Test Engineer**
1. Read: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) (entire, 25 min)
2. Reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) §5 — Debugging Checklist (2 min)
3. Execute: §7 Validation Checklist before every release
4. Monitor: §7.2 Post-Launch Monitoring checklist

### 🏗️ **I'm an Architect/Lead**
1. Read: [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) (10 min)
2. Review: [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) §2 Key Decisions (15 min)
3. Assess: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) §1 Error Categories (10 min)
4. Decide: Use DESIGN_SUMMARY.md §"When to Read Each Section" for team guidance

### 👤 **I'm Onboarding**
1. Watch: Full repo walkthrough (visual → code)
2. Read: [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) top to bottom (15 min)
3. Study: [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) to understand flows (20 min)
4. Practice: Find code locations using [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) §"Code Locations by Topic"

---

## 📖 Navigation by Question

### **"How does the system decide what to answer?"**
1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "One-Page Decision Flowchart" (1 min)
2. [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) § 1-2 (10 min)
3. [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) § 2 (30 min)

### **"What could go wrong and how do we handle it?"**
1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Safety Rules" (2 min)
2. [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) § 1-3 (30 min)
3. [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) § 6 (10 min)

### **"How do we test this?"**
1. [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) § 7 (15 min)
2. [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) § 1-6 for test patterns (60 min)
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Debugging Checklist" (5 min)

### **"What's the prompt and why?"**
1. [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) § 1 (15 min)
2. [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) § 3.2 (5 min)
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Safety Rules" (2 min)

### **"How do intents work?"**
1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Intent Routing Quick Reference" (2 min)
2. [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) § 2.1 (10 min)
3. Code: `intent_router.py` (20 min)

### **"Where's the code for X?"**
1. [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) § "Code Locations by Topic" (2 min)
2. Navigate to file using VS Code Ctrl+P

### **"Why are confidence scores different each request?"**
1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Confidence Score Reference" (2 min)
2. [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) § 2.3 (5 min)
3. [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) § 5 (5 min)

### **"How do we handle when API is down?"**
1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Safety Rules" item 4 (1 min)
2. [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) § 2.4 (8 min)
3. [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) § 4 (8 min)

---

## 🔄 Document Relationships

```
┌─────────────────────────────────────────────────────────────┐
│ README_DESIGN_DOCS.md (This file)                          │
│ ↓ Navigation hub for all docs                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ QUICK_REFERENCE.md (3 pages)                           │ │
│ │ ↓ For quick answers, debugging, common issues          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ DESIGN_SUMMARY.md (10 pages)                                │ │
│ │ ↓ Architecture overview, design decisions, code locations   │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ PROMPT_AND_DECISION_DESIGN.md (20 pages)                    │ │
│ │ ↓ Deep dive: prompts, routing, confidence, safety rules     │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ DECISION_FLOWCHART.md (15 pages)                            │ │
│ │ ↓ Visual: state machines, flowcharts, end-to-end flows      │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ ERROR_SAFETY_TEST_SCENARIOS.md (25 pages)                   │ │
│ │ ↓ Test cases, validation, safety scenarios, monitoring      │ │
│ └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Key Topics Across Documents

| Topic | Quick Ref | Summary | Deep Dive | Flowchart | Tests |
|-------|-----------|---------|-----------|-----------|-------|
| Intent Routing | ✅ | ✅ | ✅ | ✅ | ✅ |
| Evidence Gathering | ✅ | ✅ | ✅ | ✅ | ✅ |
| Prompt Composition | ✅ | ✅ | ✅ | ✅ | ❌ |
| Confidence Scoring | ✅ | ✅ | ✅ | ✅ | ✅ |
| Safety Rules | ✅ | ✅ | ✅ | ✅ | ✅ |
| Provider Fallback | ✅ | ✅ | ✅ | ✅ | ✅ |
| Error Handling | ✅ | ✅ | ✅ | ✅ | ✅ |
| Testing Strategy | ❌ | ✅ | ✅ | ❌ | ✅ |
| Performance | ❌ | ✅ | ✅ | ❌ | ✅ |
| Debugging Guide | ✅ | ✅ | ❌ | ❌ | ✅ |

---

## 🔍 Search Tips

**Use Ctrl+F to search across documents:**
- Search for **intent names**: `PAGE_QA`, `SUMMARY`, `QUIZ`, etc.
- Search for **confidence**: `confidence`, `0.95`, `abstain`
- Search for **safety**: `prompt injection`, `safety-rule`, `abstention`
- Search for **providers**: `OpenAI`, `Gemini`, `fallback`
- Search for **errors**: `HTTPException`, `ProviderError`, `timeout`
- Search for **code files**: `intent_router.py`, `answer_service.py`, etc.

---

## 🚀 Common Workflows

### Workflow 1: Understanding a User Issue

1. **Symptom**: User got wrong answer / unexpected behavior
2. **Step 1**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Debugging Checklist" (2 min)
3. **Step 2**: [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) § 3 "Answer Composition" (5 min)
4. **Step 3**: Check logs for `trace_id`, `intent`, `confidence`
5. **Step 4**: Locate code in [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) § "Code Locations"
6. **Step 5**: Debug using [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Debugging Checklist"

### Workflow 2: Adding a New Feature

1. **Goal**: Add new intent / safety rule / improvement
2. **Step 1**: [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) § "Common Modifications" (5 min)
3. **Step 2**: [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) relevant section (15 min)
4. **Step 3**: Code the change
5. **Step 4**: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) § 7 Validation Checklist
6. **Step 5**: Run `python eval/run_eval.py`, verify score ≥85%

### Workflow 3: Performance Optimization

1. **Goal**: Reduce latency or token usage
2. **Step 1**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Performance Targets" (2 min)
3. **Step 2**: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) § 6 Performance Tests (15 min)
4. **Step 3**: Identify bottleneck (router / context / LLM)
5. **Step 4**: Optimize using [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) code locations
6. **Step 5**: Measure improvement with `python eval/run_eval.py --timing`

### Workflow 4: Safety Audit

1. **Goal**: Audit and strengthen safety mechanisms
2. **Step 1**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Safety Rules" (2 min)
3. **Step 2**: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) § 2 Safety Tests (20 min)
4. **Step 3**: [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) § 3 Error Scenarios (20 min)
5. **Step 4**: Review all safety rules in code via [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md)
6. **Step 5**: Run full test suite with `pytest be/tests/`

---

## 📊 Document Statistics

| Document | Pages | Key Sections | Diagrams | Code Examples |
|----------|-------|---|----------|---|
| QUICK_REFERENCE.md | 3 | 8 | 1 | 4 |
| DESIGN_SUMMARY.md | 10 | 9 | 1 | 5 |
| PROMPT_AND_DECISION_DESIGN.md | 20 | 7 | 2 | 12 |
| DECISION_FLOWCHART.md | 15 | 8 | 8 | 2 |
| ERROR_SAFETY_TEST_SCENARIOS.md | 25 | 10 | 1 | 15 |
| **TOTAL** | **73 pages** | **42 sections** | **13 diagrams** | **38 examples** |

---

## 🔄 Keeping Documentation Current

**When you change code:**

| Change | Update | Location |
|--------|--------|----------|
| Modify prompt | § 1 PROMPT_AND_DECISION_DESIGN.md | System prompt section |
| Add intent | § 2 PROMPT_AND_DECISION_DESIGN.md + FLOWCHART § 1 | Intent table + router section |
| Add safety rule | § 3 PROMPT_AND_DECISION_DESIGN.md + § 4 FLOWCHART | Safety hierarchy section |
| Change confidence calculation | § 2.3 PROMPT_AND_DECISION_DESIGN.md + § 5 FLOWCHART | Confidence formula |
| Add test case | § 2 ERROR_SAFETY_TEST_SCENARIOS.md | Test case section |
| Move code file | DESIGN_SUMMARY.md § "Code Locations" | File navigation table |

---

## 📞 Questions?

**For questions about:**
- **"How does X work?"** → Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) first, then [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md)
- **"Where's the code for X?"** → [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) § "Code Locations by Topic"
- **"Can I do X?"** → [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) § "Common Modifications"
- **"What could go wrong?"** → [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md)
- **"How do I test X?"** → [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) § 7 Validation Checklist

---

## 📌 Quick Links to Key Sections

- **Decision Flowchart (1 minute)**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "One-Page Decision Flowchart"
- **Safety Rules (2 minutes)**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Safety Rules"
- **Intent Reference (2 minutes)**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Intent Routing Quick Reference"
- **Debugging Checklist (5 minutes)**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) § "Debugging Checklist"
- **Code Locations (5 minutes)**: [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) § "Code Locations by Topic"
- **Complete Confidence Algorithm (10 minutes)**: [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) § 5
- **Full Test Coverage (30 minutes)**: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md)

---

## 🎓 Study Path (Recommended Order)

**Day 1:**
- [ ] Read QUICK_REFERENCE.md (15 min)
- [ ] Skim DESIGN_SUMMARY.md (10 min)
- [ ] Study DECISION_FLOWCHART.md § 1-2 (20 min)

**Day 2:**
- [ ] Read PROMPT_AND_DECISION_DESIGN.md § 1-2 (40 min)
- [ ] Study DECISION_FLOWCHART.md § 3-4 (20 min)
- [ ] Code deep-dive: `orchestration_service.py` (30 min)

**Day 3:**
- [ ] Read ERROR_SAFETY_TEST_SCENARIOS.md § 1-3 (40 min)
- [ ] Run golden set: `python eval/run_eval.py` (10 min)
- [ ] Practice: Trace a user query through the system (20 min)

**Ongoing:**
- [ ] Keep QUICK_REFERENCE.md open while coding
- [ ] Reference specific sections as needed
- [ ] Update docs when you change code

---

**Created:** 2026-07-30  
**Last Updated:** 2026-07-30  
**Version:** 1.0

