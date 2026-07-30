# VLearn Tutor AI — Developer Quick Reference Card

## 🎯 One-Page Decision Flowchart

```
USER MESSAGE (Vietnamese)
          ↓
    [SAFE?] ─→ NO ─→ BLOCK: "Bỏ qua..."  (Conf: 0.1)
          ↓ YES
    [INTENT?]
          ├─→ VISUAL / SELECTION → High conf (0.95)
          ├─→ SUMMARY → Cached (no LLM)
          ├─→ QUIZ / FLASHCARD → Template (no LLM)
          ├─→ PAGE_QA / SEARCH → Retrieval + LLM
          ├─→ CLARIFY → Ask follow-up (conf: 0.55)
          └─→ OUT_OF_SCOPE → "Ngoài phạm vi"
          ↓
    [HAS EVIDENCE?]
          ├─→ NO + doc_only → ABSTAIN (Conf: 0.2)
          ├─→ NO + extended → Deterministic
          └─→ YES → Compose answer
          ↓
    [LLM AVAILABLE?]
          ├─→ YES → Call OpenAI
          │         └→ Fail? → Fallback to Gemini
          │                   └→ Fail? → Deterministic
          └─→ NO → Use template / bullet list
          ↓
    [VERIFY GROUNDING]
          ├─→ Hallucination? → Lower conf
          └─→ Out of scope? → Mark abstained
          ↓
    RETURN ChatResponseV2
    { answer, citations, confidence, trace }
```

---

## 📊 Confidence Score Reference

| Scenario | Score | When to Abstain? |
|----------|-------|------------------|
| User selected text, asks about it | 0.95 | ❌ Always answer |
| Strong keyword + doc + evidence | 0.85-0.90 | ❌ Always answer |
| Document mention + some evidence | 0.75-0.85 | ❌ Usually answer |
| Weak evidence, low keyword match | 0.50-0.65 | ⚠️ Consider abstaining |
| Ambiguous (clarify needed) | 0.55 | ⚠️ Often abstain |
| Document indexing (status guard) | 0.20 | ✅ Always abstain |
| No evidence + document_only | 0.20 | ✅ Always abstain |
| Prompt injection detected | 0.10 | ✅ Always block |

**Rule:** Abstain if confidence < 0.3 OR (document_only AND no evidence)

---

## 🛡️ Safety Rules (Execution Order)

```
1️⃣ INJECTION CHECK
   if contains_prompt_injection(message):
       return "Bỏ qua các chỉ dẫn..."
   Location: answer_service.py:30

2️⃣ EVIDENCE CHECK (document_only mode)
   if answer_mode == "document_only" and not evidence:
       return "Chưa tìm thấy..."
   Location: answer_service.py:37

3️⃣ GROUNDING VERIFICATION
   verify(answer, evidence, mode)
   Location: orchestration_service.py:147

4️⃣ PROVIDER FALLBACK
   try OpenAI → except → try Gemini → except → deterministic
   Location: llm_service.py:77-136
```

---

## 🔀 Intent Routing Quick Reference

| Keyword (Vietnamese) | Intent | Confidence |
|---|---|---|
| tóm tắt, tổng hợp, outline, key, mục tiêu học | SUMMARY | 0.90 |
| quiz, câu hỏi trắc nghiệm, kiểm tra | QUIZ | 0.86 |
| flashcard, thẻ ghi nhớ | FLASHCARD | 0.86 |
| so sánh, khác nhau, giống nhau | COMPARE | 0.84 |
| ở đâu, trang nào, vị trí, nằm đâu | FIND_LOCATION | 0.88 |
| thời tiết, bóng đá, mua cổ phiếu, đặt vé | OUT_OF_SCOPE | 0.75 |
| [page number mentioned] + document | PAGE_QA | 0.88 |
| [document loaded] + generic question | DOCUMENT_SEARCH | 0.78 |
| [text selected] | SELECTION_QA | 0.95 |
| [visual region marked] | VISUAL_QA | 0.95 |
| [ambiguous + short] | CLARIFY | 0.55 |
| [default] | GENERAL_CHAT | 0.70 |

**File:** `intent_router.py`

---

## 💻 Key Code Patterns

### Pattern 1: Routing a User Question
```python
# intent_router.py
def route(self, request: ChatRequestV2) -> tuple[Intent, float]:
    message = search_normalize(request.message)  # Remove diacritics
    
    # Check high-priority signals first
    if request.context.visual_region:
        return Intent.VISUAL_QA, 0.95
    
    # Then keyword matching
    if "tom tat" in message:
        return Intent.SUMMARY, 0.9
    
    # Fallback
    return Intent.GENERAL_CHAT, 0.7
```

### Pattern 2: Gathering Evidence
```python
# context_resolver.py
def resolve(self, request) -> ContextResolution:
    intent = router.route(request)
    
    if intent == Intent.PAGE_QA:
        evidence = self._page_context_service.extract(
            request.document_id,
            request.page_number
        )
    elif intent == Intent.DOCUMENT_SEARCH:
        evidence = self._retrieval_service.search(
            request.document_id,
            request.message
        )
    # ...
    
    return ContextResolution(
        evidence=evidence,
        confidence=calculate_evidence_confidence(evidence)
    )
```

### Pattern 3: Checking Safety Rules
```python
# answer_service.py:compose()
async def compose(self, *, message, intent, evidence, answer_mode):
    # Rule 1: Injection
    if contains_prompt_injection(message):
        return "Bỏ qua...", "deterministic", "safety-rule", False
    
    # Rule 2: Evidence requirement
    if answer_mode == "document_only" and not evidence:
        return "Chưa tìm...", "deterministic", "abstention-rule", False
    
    # Rule 3: Call LLM if available
    if self.provider_gateway.configured() and evidence:
        try:
            result, fallback = await self.provider_gateway.generate(...)
            return result.text, result.provider, result.model, fallback
        except Exception:
            pass  # Fall through to deterministic
    
    # Rule 4: Fallback to deterministic
    return self._deterministic_answer(message, intent, evidence), ...
```

### Pattern 4: Calculating Final Confidence
```python
# orchestration_service.py:chat()
confidence = max(
    route_confidence * 0.4,        # Router signal (dampened)
    verification["confidence"],    # Grounding check
    resolved.confidence            # Evidence quality
)
```

---

## 🔍 Debugging Checklist

**When answer is wrong:**
- [ ] Check intent: `response.trace.intent` — Is it routing correctly?
- [ ] Check evidence: `response.debug.evidence_ids` — Is retrieval finding right chunks?
- [ ] Check grounding: `response.debug.verification` — Any hallucinations detected?
- [ ] Check confidence: `response.confidence` — Should we have abstained?

**When latency is high (>3s):**
- [ ] Check `response.trace.latency_ms` breakdown
- [ ] Is retrieval slow? (typically takes 50-200ms)
- [ ] Is LLM slow? (typically takes 500-2000ms)
- [ ] Is embedding model loading? (first call: ~5s)

**When user sees "Bỏ qua chỉ dẫn...":**
- [ ] User tried prompt injection
- [ ] Check logs: `python -c "from app.services.text_utils import contains_prompt_injection; print(contains_prompt_injection('your message'))"`

**When no evidence found:**
- [ ] Check document status: `GET /api/documents/{id}/status`
- [ ] If INDEXING: Document still processing
- [ ] If READY: Search likely returned no results (try different keywords)
- [ ] If ERROR: PDF format not supported

---

## 📝 User-Facing Messages (Vietnamese)

| Situation | Message |
|-----------|---------|
| No evidence, document_only mode | "Mình chưa tìm thấy đủ căn cứ trong tài liệu để trả lời câu này." |
| Low confidence but has evidence | "Mình có ít căn cứ cho câu hỏi này. Đây là những gì mình tìm được: ..." |
| Document still indexing | "Tài liệu đang được xử lý. Hãy đợi đến khi trang thái READY rồi hỏi lại." |
| Out of scope | "Chủ đề này ngoài phạm vi của khóa học. Hãy hỏi về nội dung tài liệu." |
| Injection attempt | "Mình sẽ bỏ qua các chỉ dẫn có tính thay đổi hệ thống. Hãy đặt câu hỏi về nội dung tài liệu." |
| Both providers failed | "OpenAI đang tạm thời không khả dụng và Gemini fallback cũng thất bại." |

---

## 🔗 File Navigation

### By Feature

**Routing:**
- `intent_router.py` — 9 intent types
- `domain/intents.py` — Intent enum

**Context & Evidence:**
- `retrieval_service.py` — Hybrid search
- `page_context_service.py` — Page extraction
- `visual_context_service.py` — Visual regions
- `summary_service.py` — Cached summaries

**Answer Composition:**
- `answer_service.py` — Message building + deterministic templates
- `llm_service.py` (OLD) — Legacy implementation
- `provider_gateway.py` — Provider orchestration

**Safety & Quality:**
- `text_utils.py` — Injection detection, normalization
- `grounding_service.py` — Hallucination check, verification

**Main Pipeline:**
- `orchestration_service.py` — Complete chat flow (200 lines, study this first)
- `routers/chat_v2.py` — API endpoint

### By Task

**Adding a new intent:**
1. `domain/intents.py` — Add enum value
2. `intent_router.py` — Add routing logic
3. `orchestration_service.py` — Add handler
4. Tests

**Changing prompt:**
1. `answer_service.py:SYSTEM_PROMPT_V2` — Update system instruction
2. Test golden set

**Adding safety rule:**
1. `answer_service.py:compose()` — Add rule
2. Add test case in `tests/unit/test_prompt_injection.py`

**Improving retrieval:**
1. `retrieval_service.py` — Hybrid search (lexical + dense)
2. `reranker_service.py` — Re-rank top-k results

---

## 📊 Golden Set Evaluation

```bash
# Run evaluation
python eval/run_eval.py

# Expected output:
# Total: 31/31 cases
# Pass rate: >= 85%
# Coverage by intent:
#   PAGE_QA: 5/5
#   SUMMARY: 3/3
#   QUIZ: 2/2
#   ... etc
```

**If score < 85%:**
1. Identify which intents are failing
2. Check if retrieval is broken (new ranking?)
3. Check if prompt changed (LLM behavior)
4. Review specific failing cases and fix

---

## 🚀 Deployment Checklist

```
PRE-DEPLOY
[ ] Golden set score >= 85%
[ ] All tests pass (pytest)
[ ] No API keys in code
[ ] .env configured correctly

DURING DEPLOY
[ ] Stop old backend gracefully
[ ] Start new backend
[ ] Verify health: GET /api/health
[ ] Warm up cache: Run 5 queries

POST-DEPLOY
[ ] Monitor error rate (target: <1%)
[ ] Monitor latency p95 (target: <3500ms)
[ ] Check for new injection attempts
[ ] Review logs for anomalies
```

---

## ⚡ Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Router latency | <10ms | ~5ms |
| Context resolution | <200ms | ~50-150ms |
| LLM call | <3000ms | ~800ms (gpt-4) |
| **Total (p95)** | **<3200ms** | **~2000ms** |
| **Tokens per request** | **<4000** | **~3600** |

---

## 🐛 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Confidence always 0.1 | Injection filter too aggressive | Check `text_utils.py` regex patterns |
| Latency > 5s | Embedding model not cached | Warm up on startup, check disk space |
| No fallback to Gemini | Config error | Verify `ENABLE_GEMINI_FALLBACK=true` in .env |
| Citations wrong pages | Evidence ranking broken | Check `reranker_service.py` |
| Same answer for all queries | History not clearing | Verify `conversation_id` unique |

---

## 📚 Full Documentation

- **[PROMPT_AND_DECISION_DESIGN.md](PROMPT_AND_DECISION_DESIGN.md)** — Deep dive into prompts & logic
- **[DECISION_FLOWCHART.md](DECISION_FLOWCHART.md)** — Visual flowcharts & diagrams
- **[ERROR_SAFETY_TEST_SCENARIOS.md](ERROR_SAFETY_TEST_SCENARIOS.md)** — Test cases & validation
- **[DESIGN_SUMMARY.md](DESIGN_SUMMARY.md)** — Navigation guide

---

**Last Updated:** 2026-07-30  
**Status:** Production Reference Card
