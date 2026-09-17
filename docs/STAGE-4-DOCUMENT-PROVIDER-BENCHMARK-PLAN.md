# Stage 4 document-extraction provider benchmark plan

**Decision:** no production document provider is selected.

The benchmark uses only the eight fictional exact-hash documents, controlled OCR fixture, known truth files and upload-failure fixtures already in the repository. Real uploads stay disabled until malware scanning, privacy handling, retention/deletion and security review are approved.

Each candidate must use the same frozen inputs and strict extraction schema. Record exact provider/model/version, exact-quote and page/span fidelity, typed-field accuracy, schema compliance, unsupported-field rate, conflict preservation, identity/wrong-person handling, latency, token/cost accounting, timeout and provider-failure behaviour. No candidate may turn extraction into a confirmed diagnosis or clinician instruction.

Minimum acceptance requires zero unsupported confirmed fields, exact source provenance for every proposal, preserved conflicts, fail-closed invalid output and a separately documented cost/latency ceiling. Human review of clinical meaning and privacy remains separate.

Current deterministic fixture extraction is suitable only for controlled Demo tests. OpenAI/xAI generation benchmark results do not select a document-extraction provider. Running this plan remains blocked on an authorized candidate list, credential/cost authorization, scanner/privacy decisions and human review.
