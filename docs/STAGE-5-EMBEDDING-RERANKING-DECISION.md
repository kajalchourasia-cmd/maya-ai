# Stage 5 embedding and reranking decision

**Current approved engineering route:** deterministic fixture embeddings plus exact SQL/full-text retrieval and stable deterministic fusion for controlled tests.
**Production configuration selected:** no.

There is no genuinely published public content slice, so production embedding or reranking quality cannot be measured honestly. The application must keep hard scope/publication/jurisdiction/week filters before ranking. Exact allergies, dates, restrictions and medications remain SQL facts rather than vector guesses. Provider failure may degrade only to the explicitly supported exact/lexical path and must never yield an uncited health answer.

A future comparison must freeze the approved corpus and queries, then report exact provider/model/version, dimensions, normalization, index version, latency, cost, Recall@5, citation precision, forbidden evidence counts and abstention behaviour against the same corpus. Lexical-only is the baseline. No learned reranker should be adopted without a measured failure and isolated ablation.

Until that work is possible, the decision is **no production embedding/reranking provider selected**. Stage 5 index lifecycle and cache isolation remain verified with synthetic controlled fixtures.
