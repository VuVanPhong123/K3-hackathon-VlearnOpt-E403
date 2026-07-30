# VLearn Tutor Eval

`golden_set.jsonl` contains 31 cases: exact page QA, selected text, whole-document search, location finding, summary, compare, visual region, typo, ambiguous follow-up, no-answer, small talk, prompt injection, provider fallback, and scanned/no-text page.

At least 10 cases are derived from anonymized VLearn chatlog IDs, referenced by `conversation_id` and `turn_id` only.

Run:

```bash
python eval/run_eval.py
```

The deterministic runner does not call live providers. Optional LLM judging can be added later when API keys are available.
