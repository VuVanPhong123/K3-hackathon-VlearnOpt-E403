# VLearn Tutor — Offline Evaluation Report

## Run metadata

| Field | Value |
|---|---|
| Generated | 2026-07-30T17:45:01+07:00 |
| Git SHA | `ef502143cca7066aa203a22c2bbd04258efa8e4a` |
| Working tree | dirty (kết quả trước commit) |
| Python | `3.11.8` |
| Platform | `Windows-10-10.0.26200-SP0` |
| Golden set | `eval\golden_set.jsonl` |
| Golden SHA-256 | `0cf17c8c3c390ff45adf67d46cdec2a70e5241eb590bd3f12d2c4d079f579443` |
| Raw report | `eval\results\latest.json` |
| Execution mode | Offline, deterministic `RecordingProvider` |
| Retrieval in eval | Fixture chunks + hash embedding |

## Quality dimensions

| Dimension | Reproducible pass condition |
|---|---|
| `status` | HTTP status khớp expected. |
| `mode` | Chế độ tương tác khớp expected. |
| `page_context` | Trang dùng đúng tập trang bắt buộc và không dùng trang cấm. |
| `citation` | Citation có/không và số trang khớp expected. |
| `provider_invocation` | Có hoặc không gọi provider đúng như expected. |
| `media_path` | Đường gọi text/multimodal và việc đính ảnh khớp expected. |
| `fallback` | Provider, fallback và thứ tự provider khớp expected. |
| `prompt_context` | Prompt chứa đủ chuỗi bắt buộc và không chứa chuỗi cấm. |
| `history_limit` | Số message lịch sử không vượt giới hạn expected. |
| `utf8_response` | Output tiếng Việt giữ được ký tự có dấu. |
| `error_detail` | Thông báo lỗi chứa đủ nội dung bắt buộc. |
| `decision` | Decision answer/clarify/abstain khớp expected. |
| `clarification` | Cờ needs_clarification khớp expected. |
| `abstention` | Cờ abstained khớp expected. |
| `no_crash` | Case kết thúc có kiểm soát, không phát sinh exception ngoài contract. |

## Quality bar result

| Metric | Actual | Threshold | Result |
|---|---:|---:|:---:|
| `overall_case_pass_rate` | 100.0% | 90.0% | PASS |
| `status_accuracy` | 100.0% | 100.0% | PASS |
| `mode_accuracy` | 100.0% | 95.0% | PASS |
| `page_context_accuracy` | 100.0% | 95.0% | PASS |
| `citation_accuracy` | 100.0% | 95.0% | PASS |
| `provider_invocation_accuracy` | 100.0% | 100.0% | PASS |
| `media_path_accuracy` | 100.0% | 100.0% | PASS |
| `fallback_accuracy` | 100.0% | 100.0% | PASS |
| `prompt_context_accuracy` | 100.0% | 95.0% | PASS |
| `history_limit_accuracy` | 100.0% | 100.0% | PASS |
| `utf8_response_accuracy` | 100.0% | 100.0% | PASS |
| `error_detail_accuracy` | 100.0% | 100.0% | PASS |
| `decision_accuracy` | 100.0% | 100.0% | PASS |
| `clarification_accuracy` | 100.0% | 100.0% | PASS |
| `abstention_accuracy` | 100.0% | 100.0% | PASS |
| `no_crash_rate` | 100.0% | 100.0% | PASS |

**Overall quality bar:** PASS

## Complete case table

| Case | Source | Layer | Tier | Applicable checks | Result | Failed dimensions |
|---|---|:---:|---|---|:---:|---|
| `page_real_C0021_T0769` | `vlearn_chatlog_adapted` | 1_truth | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `visual_real_C0023_T0399` | `vlearn_chatlog_adapted` | 4_domain | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `page_real_C0001_T0649` | `vlearn_chatlog_adapted` | 1_truth | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `selection_real_C0015_T0811` | `vlearn_chatlog_adapted` | 1_truth | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `selection_real_C0002_T0092` | `vlearn_chatlog_adapted` | 1_truth | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `summary_real_C0031_T0408` | `vlearn_chatlog_adapted` | 1_truth | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `summary_real_C0076_T1258` | `vlearn_chatlog_adapted` | 1_truth | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `page_real_C0228_T1023` | `vlearn_chatlog_adapted` | 1_truth | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `page_real_C0266_T1084` | `vlearn_chatlog_adapted` | 1_truth | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `visual_real_C0547_T0135` | `vlearn_chatlog_adapted` | 4_domain | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `general_no_document` | `synthetic` | 3_scope_authority | routine | status, mode, page_context, citation, provider_invocation, media_path, fallback, utf8_response, no_crash | PASS | — |
| `general_forced_with_document` | `synthetic` | 3_scope_authority | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `smalltalk_hi_with_document` | `synthetic` | 3_scope_authority | routine | status, mode, page_context, citation, provider_invocation, media_path, fallback, utf8_response, no_crash | PASS | — |
| `smalltalk_thanks_with_document` | `synthetic` | 3_scope_authority | routine | status, mode, page_context, citation, provider_invocation, media_path, fallback, utf8_response, no_crash | PASS | — |
| `general_allowed_with_document` | `synthetic` | 3_scope_authority | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `forced_search_without_document` | `synthetic` | 3_scope_authority | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, utf8_response, no_crash | PASS | — |
| `history_limit_general` | `synthetic` | 2_ambiguity | hard | status, mode, provider_invocation, media_path, fallback, prompt_context, history_limit, utf8_response, no_crash | PASS | — |
| `page_attached_standard` | `synthetic` | 1_truth | routine | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `page_explicit_multi_head` | `synthetic` | 1_truth | routine | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `page_active_current` | `synthetic` | 2_ambiguity | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `page_forced_active` | `synthetic` | 2_ambiguity | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `page_out_of_range` | `synthetic` | 2_ambiguity | hard | status, provider_invocation, error_detail, no_crash | PASS | — |
| `page_multiple_attached` | `synthetic` | 2_ambiguity | rare | status, provider_invocation, error_detail, no_crash | PASS | — |
| `page_missing_document` | `synthetic` | 2_ambiguity | hard | status, provider_invocation, error_detail, no_crash | PASS | — |
| `page_visual_question` | `synthetic` | 4_domain | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `selection_valid` | `synthetic` | 1_truth | routine | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `selection_priority_over_page` | `synthetic` | 2_ambiguity | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `selection_forged` | `synthetic` | 1_truth | rare | status, provider_invocation, error_detail, no_crash | PASS | — |
| `selection_forced` | `synthetic` | 2_ambiguity | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, utf8_response, no_crash | PASS | — |
| `visual_region_standard` | `synthetic` | 4_domain | routine | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `visual_priority_over_selection` | `synthetic` | 2_ambiguity | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `search_exact_figure` | `synthetic` | 4_domain | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `search_training_chart` | `synthetic` | 4_domain | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `search_rag` | `synthetic` | 1_truth | routine | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `search_scaled_attention` | `synthetic` | 1_truth | routine | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `search_multi_head` | `synthetic` | 1_truth | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `search_table_comparison` | `synthetic` | 4_domain | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `search_grounded_abstention` | `synthetic` | 1_truth | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, no_crash | PASS | — |
| `fallback_text_temporary` | `synthetic` | 3_scope_authority | hard | status, mode, provider_invocation, media_path, fallback, utf8_response, no_crash | PASS | — |
| `provider_text_request_error` | `synthetic` | 3_scope_authority | hard | status, provider_invocation, fallback, error_detail, no_crash | PASS | — |
| `fallback_vision_temporary` | `synthetic` | 3_scope_authority | rare | status, mode, page_context, citation, provider_invocation, media_path, fallback, utf8_response, no_crash | PASS | — |
| `provider_credentials_missing` | `synthetic` | 3_scope_authority | rare | status, provider_invocation, error_detail, no_crash | PASS | — |
| `utf8_response_contract` | `synthetic` | 4_domain | routine | status, mode, provider_invocation, media_path, fallback, utf8_response, no_crash | PASS | — |
| `clarify_forced_search_missing_document` | `synthetic` | 2_ambiguity | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, decision, clarification, abstention, no_crash | PASS | — |
| `search_no_evidence_abstains` | `synthetic` | 2_ambiguity | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, utf8_response, decision, clarification, abstention, no_crash | PASS | — |
| `search_no_evidence_allow_general` | `synthetic` | 3_scope_authority | hard | status, mode, page_context, citation, provider_invocation, media_path, fallback, prompt_context, utf8_response, decision, clarification, abstention, no_crash | PASS | — |

## Failed cases

- Không có.

## Scope and limitations

- Report này đo routing, context priority, citation contract, provider/fallback path, conditional decision và khả năng không crash.
- `RecordingProvider` trả output định sẵn; report này không chứng minh chất lượng ngôn ngữ hoặc semantic groundedness của model thật.
- API thật và multimodal thật được chứng minh riêng trong `evidence/r5-live-ai-run.md`.
- Không có API key, header, PDF/base64 hoặc raw chatlog trong report.
