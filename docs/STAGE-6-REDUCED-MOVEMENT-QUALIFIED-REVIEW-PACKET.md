# Reduced-movement qualified safety-policy review packet

**Specification:** `data/safety/rule_spec.yaml` version 1.0.0, status `draft`, jurisdiction IN, English scope.
**Live/public status:** blocked. Runtime must fail closed.
**Engineering invariant:** both example paths make zero ordinary-generation calls.

## Current observed contract

| Input | Current controlled-fixture route | Match | Required status |
|---|---|---|---|
| “I feel reduced movement right now” | `needs_clarification` | no configured rule; generic symptom/medical ambiguity fallback | Keep ordinary generation blocked; qualified policy decision pending. |
| “My baby is moving less than usual right now” | evaluation-only `urgent` | draft fetal-movement rule | Do not publish final urgent wording/routing without qualified review. |

## Review questions

- What gestational applicability and exclusions are clinically appropriate?
- Which paraphrases, misspellings and common English/Hinglish expressions must route urgently versus clarify?
- What immediate wording is safe, action-first and appropriate for India?
- Which local emergency or maternity-service route may be stated and with what source/currentness?
- What negative/historical/quoted/third-person cases must not be attributed to the user?
- Is the fixed message acceptable, or what exact versioned replacement is approved?

## Decision record

Reviewer name: **pending**
Role and relevant qualification: **pending**
Decision: **pending**
Exact approved wording/rule changes: **pending**
Sources/locators: **pending**
Decision date and next review date: **pending**

Codex has not added or self-approved a clinical rule. The conservative stop remains until a genuine qualified decision is imported and regression-tested.
