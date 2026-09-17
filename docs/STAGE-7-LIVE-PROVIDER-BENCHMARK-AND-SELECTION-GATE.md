# Stage 7 live-provider benchmark and selection gate

**Frozen dataset:** `stage7-live-provider-fictional-v1`, 8 fictional cases.
**Authorization reference:** `user-authorized-live-provider-benchmark-2026-09-12`.
**Provider selected for Personal Mode:** **none**.

The adapter sends only the bounded canonical draft/evidence identifiers needed to rewrite a deterministic summary. It uses strict structured output, provider/model identity checks, time/output/cost ceilings, redacted failure handling, no tools and no write authority. There is no automatic fixture fallback in Personal Mode.

## Measured candidate results

| Candidate | Access check | Completed | Stage 8 displayed | Citation/support check | Urgent + clarify | Cost | Latency | Human tone review | Decision |
|---|---|---:|---:|---:|---:|---:|---|---:|---|
| xAI `grok-4.6` | key and model-list access succeeded | 6/8 | 4/8 | 6/8 | 2/2 with zero calls | $0.020862 | median 4299.24 ms; p95 5926.12 ms | 0/8 complete | Do not select |
| OpenAI `gpt-5.4-mini` | key and model-list access succeeded | 2/8 | 0/8 | 2/8 | 2/2 with zero calls | $0 | called cases fail closed | 0/8 complete | Blocked; do not select |

xAI passed nutrition, movement, record and follow-up display routes. The medication case returned a provider failure. The combined-plan case completed four contributors and failed closed at composition. Immediate bounded diagnostics later produced valid structured medication and composer responses, showing provider/model variability; the original 6/8 result remains the selection evidence and was not overwritten.

OpenAI exposed the selected model in its official model list, but every called case failed closed. A direct redacted diagnostic returned HTTP 429 indicating that API credits were unavailable. This remained true after the user reported adding credits, so billing/project credit propagation must be rechecked before another authorized run. No credential value is in this report.

Provider failure is distinct from a constraint escape. The first generated aggregate incorrectly counted any incomplete case as an allergy/restriction/medication violation. The benchmark generator was corrected: outages and invalid structured responses remain failed cases, while the violation metric counts only an actually displayed boundary escape. No unsafe failed draft was displayed.

## Retry boundary

The current canonical Stage 7 budget permits at most one specialist generation call. The transport therefore fails closed after a failed call rather than silently spending a second model call. Adding a network retry would materially change that budget and is not self-authorized in this pass. The provider interface exposes retry accounting, and a future reviewed budget may permit one bounded retry.

## Selection rule

A provider cannot be selected until the same frozen dataset completes, automated safety/schema/evidence/constraint gates pass, the manual tone/usability sample is reviewed, cost/latency are accepted and an actually available fallback is measured. Access or credits alone are not selection evidence.
