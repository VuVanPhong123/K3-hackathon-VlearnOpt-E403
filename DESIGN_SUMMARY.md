# VLearn Tutor AI — Design Summary & Quick Links
*A concise overview of prompt design, conditional logic, and error handling architecture*

---

## What's Been Documented

This design package contains **4 comprehensive guides** covering the entire AI decision-making pipeline:

| Document | Focus | Key Audiences |
|----------|-------|---------------|
| **[PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md)** | Prompt engineering, decision logic, confidence scoring | ML Engineers, Prompt Designers |
| **[DECISION_FLOWCHART.md](DECISION_FLOWCHART.md)** | Visual flowcharts and state diagrams | Developers, Product Managers |
| **[ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md)** | Test cases, safety validation, error scenarios | QA, Test Engineers |
| **[DESIGN_SUMMARY.md](DESIGN_SUMMARY.md)** | This file — Quick navigation & summary | Everyone |

---

## Quick Navigation

### For Different Roles

**🔍 If you're debugging a user issue:**
1. Start: [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) — Find the flow that applies
2. Dive: [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) — Understand the decision
3. Check: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) — See if it's a known case

**✍️ If you're improving the prompt:**
1. Start: [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) §1 — Prompt architecture
2. Check: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) — See what could go wrong
3. Validate: Add test case, ensure golden set score ≥ 85%

**🛡️ If you're adding a safety rule:**
1. Start: [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) §3 — Safety rules hierarchy
2. Visualize: [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) §6 — Where does it fit?
3. Test: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) §2 — Add safety test case

**🧪 If you're testing/QA:**
1. Start: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) — Test framework
2. Reference: [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) — Understand flows
3. Checklist: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) §7 — Validation checklist

**🚀 If you're deploying changes:**
1. Check: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) §7.1 — Pre-release checklist
2. Monitor: [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md) §7.2 — Post-launch monitoring

---

## Core Architecture at a Glance

```
USER INPUT (Vietnamese) 
    ↓ [§1]
[INTENT ROUTER] 
    intent: PAGE_QA / SUMMARY / VISUAL_QA / ... (confidence: 0.55-0.95)
    ↓ [§2]
[CONTEXT RESOLVER] 
    evidence: [chunks from doc], confidence: 0.3-0.95
    ↓ [§3]
[SAFETY RULES]
    ✓ Injection check → Block if detected
    ✓ Evidence check → Abstain if document_only + no evidence
    ✓ Status check → Wait if document still indexing
    ↓ [§4]
[ANSWER SERVICE]
    ├─ Deterministic: templates for FIND_LOCATION, QUIZ, FLASHCARD
    └─ LLM: gpt-4 (or Gemini fallback) for complex reasoning
    ↓ [§5]
[GROUNDING SERVICE]
    ✓ Verify citations + detect hallucinations
    ↓ [§6]
[CONFIDENCE SCORE]
    max(router_conf * 0.4, verification_conf, evidence_conf)
    ↓
[RESPONSE]
    ChatResponseV2 { answer, citations, confidence, trace, conversation_id }
```

**Files in codebase that implement this:**
- Router: `services/intent_router.py`
- Evidence: `services/context_resolver.py`, `services/retrieval_service.py`
- Safety: `services/answer_service.py` (lines 30-42), `text_utils.py`
- Answer: `services/answer_service.py:compose()`
- Verification: `services/grounding_service.py`
- Orchestration: `services/orchestration_service.py` (main pipeline)

---

## Key Design Decisions

### 1. Why Three Confidence Sources?
**Router (0.55-0.95) + Verification (0.4-0.9) + Evidence (0.3-0.95)**
- No single signal is perfect → Use all three, take max
- Prevents over-confidence from routing while evidence is weak
- Balances speed (router) with correctness (verification + evidence)

### 2. Why Deterministic for QUIZ/FLASHCARD?
- Cost: ~500ms LLM call vs <50ms template
- Predictability: Same format every time (better UX)
- Reliability: Works even if LLM is down
- Trade-off: Lower quality, but sufficient for these formats

### 3. Why Fallback Chain (OpenAI → Gemini → Deterministic)?
- Availability: If OpenAI rate-limited, Gemini often still available
- Cost: Gemini sometimes cheaper, saves on quota
- Graceful: Last resort is deterministic (always works)
- Transparency: User doesn't see provider difference

### 4. Why 8-Message History Limit?
- **Tokens**: ~1600 tokens saved vs. full history (~3200)
- **Recency bias**: Last 2-3 user turns capture most context
- **Cost**: ~$0.005 per request saved
- **Trade-off**: Multi-turn conversations can lose context after 8 messages

### 5. Why `max()` for Confidence, Not `mean()`?
- **Interpretation**: "At least one strong reason to trust"
- **Example**: Router=0.4, Evidence=0.9 → Confidence=0.9 (not 0.65)
- **Alternative `mean()`**: Would drag down confidence unnecessarily
- **Safety**: Conservative when all signals are weak (all <0.5 → all stay <0.5)

---

## Common Decisions in Code

### Deciding to Answer vs Abstain

**ANSWER (compose with LLM) when:**
```python
✓ evidence.count >= 1
✓ confidence >= THRESHOLD (typically 0.4)
✓ NOT prompt_injection
✓ NOT (document_only AND missing_evidence)
✓ document_status in ["READY", "NEEDS_INDEX"]
```

**ABSTAIN when:**
```python
✗ no evidence AND document_only mode
✗ confidence < 0.3
✗ document status INDEXING/ERROR/UPLOADING
✗ grounding_service.should_abstain() returns True
```

**BLOCK (safety) when:**
```python
✗ contains_prompt_injection(message)
✗ (Can add more rules here)
```

**File:** `orchestration_service.py:chat()` lines 111-145

---

### When to Use Each Intent Handler

| Intent | Handler Type | When Routed |
|--------|--------------|-------------|
| **PAGE_QA** | Context Resolver | `page_number` in message \| `attached_pages` in context |
| **SELECTION_QA** | Context Resolver | `text_selection.selected_text` non-empty |
| **VISUAL_QA** | Visual Service | `visual_region` present |
| **SUMMARY** | Cached Service | Keywords: "tóm tắt", "tổng hợp", "outline" |
| **QUIZ** | Template | Keywords: "quiz", "câu hỏi trắc nghiệm" |
| **FLASHCARD** | Template | Keywords: "flashcard", "thẻ ghi nhớ" |
| **DOCUMENT_SEARCH** | Retrieval | `document_id` present, no page spec |
| **FIND_LOCATION** | Template | Keywords: "ở đâu", "trang nào", "vị trí" |
| **CLARIFY** | Ask Follow-up | Short message + ambiguous pronouns |
| **OUT_OF_SCOPE** | Reject | Keywords: "thời tiết", "bóng đá", "mua cổ phiếu" |
| **GENERAL_CHAT** | Fallback | No document or no specific intent |

**File:** `intent_router.py`

---

## Safety Rules in Priority Order

```
1. PROMPT INJECTION (Highest Priority)
   ├─ Checked FIRST in answer_service.compose()
   ├─ Returns: "Mình sẽ bỏ qua các chỉ dẫn..."
   └─ Confidence: 0.1
   
2. DOCUMENT-ONLY EVIDENCE
   ├─ If answer_mode == "document_only" AND not evidence
   ├─ Returns: "Mình chưa tìm thấy đủ căn cứ..."
   └─ Confidence: 0.2
   
3. DOCUMENT STATUS
   ├─ If document UPLOADING/INDEXING/ERROR AND no evidence
   ├─ Returns: "Tài liệu đang được xử lý..."
   └─ Confidence: 0.2
   
4. GROUNDING VERIFICATION
   ├─ After answer generated, verify against evidence
   ├─ If hallucination detected → lower confidence
   └─ If scope violated → abstain
   
5. PROVIDER AVAILABILITY (Fallback)
   ├─ If primary provider fails → try secondary
   ├─ If both fail → return deterministic template
   └─ Never crash to user (always graceful)
```

**Files:** `answer_service.py:compose()`, `orchestration_service.py:chat()`

---

## Error Recovery Paths

### When No Evidence Found
```
answer_mode = "document_only" + evidence = []
    ↓
Return: "Mình chưa tìm thấy đủ căn cứ trong tài liệu để trả lời..."
Provider: "deterministic"
Model: "abstention-rule"
Confidence: 0.2
Status Code: 200 (not an error, intentional abstention)
```

### When OpenAI Rate Limited
```
ProviderRateLimitError raised
    ↓
Log: "OpenAI temporary error, attempting Gemini fallback"
    ↓
Try: GeminiProvider().generate(...)
    ↓
If success: Return Gemini answer, mark fallback=True
If fail: Raise HTTPException(503, "OpenAI dan Gemini cả thất bại")
```

### When Document Still Indexing
```
document.status = "INDEXING" AND no evidence
    ↓
Return: "Tài liệu đang được xử lý. Hãy đợi đến READY..."
Confidence: 0.2
Abstained: True
Model: "status-guard"
→ User sees wait message, tries again later
```

**File:** `orchestration_service.py` §3.4

---

## Validation & Testing

### Golden Set Baseline
- **31 test cases** across 9 intents
- **Target score**: ≥85% pass rate
- **Key metrics**:
  - Citation accuracy: ≥90% (cited pages match evidence)
  - Hallucination rate: ≤5% (entities not in evidence)
  - Latency p95: <3200ms

### Pre-Release Checklist
```bash
✅ All unit tests pass
✅ All integration tests pass
✅ Golden set score ≥85%
✅ No new prompt injections bypass
✅ Latency p95 <3200ms
✅ Fallback chain tested
✅ .env not committed
```

### Post-Launch Monitoring
```
Daily:   Error rate <1%, Latency p95 <3500ms
Weekly:  Golden set re-eval, User feedback
Monthly: Confidence calibration drift, Cost analysis
```

---

## When to Read Each Section

### [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md)

**Read §1** if:
- Improving system prompt
- Adjusting evidence formatting
- Changing history length

**Read §2** if:
- Understanding intent routing logic
- Adding new intent
- Modifying confidence calculation

**Read §3** if:
- Adding safety rule
- Understanding error handling
- Debugging injection bypass

**Read §4** if:
- Writing test cases
- Understanding golden set
- Analyzing quality metrics

### [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md)

**Read § 1-2** if:
- Visualizing user journey
- Training new developer

**Read §3-4** if:
- Debugging answer composition
- Understanding fallback chain

**Read §5-8** if:
- End-to-end flow analysis
- Testing specific scenario

### [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md)

**Read §1-2** if:
- Writing error test cases
- Understanding failure modes

**Read §3** if:
- Validating confidence scores
- Regression testing

**Read §6-7** if:
- Performance tuning
- Release validation

---

## Code Locations by Topic

### Prompt & LLM Composition
- `services/llm_service.py` — System prompt, history management
- `services/answer_service.py` — Message formatting, answer composition
- `services/provider_gateway.py` — Provider selection

### Routing & Intent
- `services/intent_router.py` — Intent detection (9 intents)
- `domain/intents.py` — Intent enum

### Evidence & Context
- `services/context_resolver.py` — Evidence gathering orchestration
- `services/retrieval_service.py` — Hybrid (lexical + dense) search
- `services/page_context_service.py` — Page-specific extraction
- `services/visual_context_service.py` — Visual region handling

### Safety & Validation
- `text_utils.py` — `contains_prompt_injection()`, normalization
- `services/grounding_service.py` — Hallucination detection, verification
- `services/answer_service.py:compose()` — Safety rule execution

### Orchestration & Pipeline
- `services/orchestration_service.py` — Main chat() pipeline
- `routers/chat_v2.py` — API endpoint

### Testing
- `tests/unit/` — Component tests
- `tests/integration/` — End-to-end flows
- `eval/run_eval.py` — Golden set evaluation

---

## Common Modifications

### Adding a New Intent

1. **Add enum** in `domain/intents.py`:
   ```python
   class Intent(StrEnum):
       YOUR_NEW_INTENT = "YOUR_NEW_INTENT"
   ```

2. **Add routing** in `intent_router.py:route()`:
   ```python
   if keyword_trigger_here:
       return Intent.YOUR_NEW_INTENT, 0.85
   ```

3. **Add handler** in `orchestration_service.py:chat()`:
   ```python
   if intent == Intent.YOUR_NEW_INTENT:
       # ... your logic ...
   ```

4. **Add test case** in `tests/` and `eval/golden_set.py`

### Adjusting Confidence Thresholds

**Location:** `orchestration_service.py:chat()` line 148
```python
confidence = max(
    route_confidence * 0.4,        # ← Adjust weight here
    verification["confidence"],
    resolved.confidence
)
```

**Factors:**
- Lower threshold (0.3) → More answers, more hallucinations
- Higher threshold (0.6) → Fewer answers, better quality
- Target: Calibrate to match actual accuracy

### Adding a Safety Rule

**Location:** `answer_service.py:compose()` lines 30-42
```python
if your_new_safety_check(message):
    return (
        "Your user-friendly error message in Vietnamese",
        "deterministic",
        "your-rule-name",
        False,
    )
```

Then add test case in `ERROR_SAFETY_TEST_SCENARIOS.md`

---

## Questions & Debugging Guide

**Q: Why did the user get answer when document is still indexing?**
A: Check `document.status` in orchestration_service.py line 111. If status is READY/NEEDS_INDEX, answer proceeds. If retrieval still found evidence, no guard triggers.

**Q: Why is confidence 0.2?**
A: Check which path was taken (line 148). Most likely: status-guard (document indexing), abstention-rule, or injection detected.

**Q: Why did it use Gemini instead of OpenAI?**
A: OpenAI threw ProviderRateLimitError or ProviderTemporaryError, fallback triggered. Check logs for "Gemini fallback".

**Q: Why is latency so high (>5000ms)?**
A: Check trace.latency_ms breakdown. Likely culprits: embedding service slow, LLM slow, retrieval slow. Profile each component.

**Q: Why did injection attempt get through?**
A: Pattern regex in `text_utils.py:contains_prompt_injection()` may not have caught it. Update patterns or add semantic check.

---

## Keeping This Documentation Up-to-Date

When you make a change:

1. **If you modify prompt**: Update [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) §1
2. **If you add routing logic**: Update [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) §2 + [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md)
3. **If you add safety rule**: Update [PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md) §3 + [DECISION_FLOWCHART.md](DECISION_FLOWCHART.md) §6
4. **If you add test case**: Update [ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md)
5. **If you add code location**: Update **Code Locations by Topic** section (above)

---

## Document Version & Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-07-30 | Claude Code | Initial version: 4 documents covering complete pipeline |

---

**Need help?** Refer to the relevant section above, then dive into the full document.

