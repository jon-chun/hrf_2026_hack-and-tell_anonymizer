# Summary report: anonymizing long-form text

Date: 2026-11-04. Reviewed source: `dev/chat_anon_v1_grok _20261104.md`.

## 1. Bottom line
The Grok chat is sound on strategy but unsafe to build from as written. Its core advice holds: detect locally, use consistent realistic surrogates, and keep an encrypted mapping. It omits credentials entirely, gives no threat model, overstates two models, and recommends a seeding method open to a dictionary attack.

This folder now holds a working three-pass tool, built as Claude Code skills. On documents written without sight of the code, passes 1 and 2 leaked 12% of known sensitive values. One audit round cleared all of those. That result comes from a small synthetic set, and it does not make the output safe to publish without a person reading it.

## 2. Measured results
All documents are synthetic and each ran alone, with no denylist. A leak means a known sensitive value still appears as a whole word.

| Test | Known values | Leaked after passes 1 and 2 | Leaked after audit | Keep-words wrongly replaced |
|---|---|---|---|---|
| Blind set 2, final rules, the number to trust | 81 | 10 (12%) | 0 | 15 of 26 |
| Blind set 1, before any tuning | 194 | 59 (30%) | not run | 15 of 32 |
| Blind set 1, after tuning on it, not blind | 194 | 21 (11%) | 2 | 8 of 32 |
| Development fixtures, tuned, not blind | 121 | 3 | not run | 0 of 79 |

| Auditor measure | Result |
|---|---|
| Remaining leaks caught, blind set 2 | 10 of 10 |
| Remaining leaks caught, blind set 1 with the final prompt | 20 of 21 |
| False alarms on surrogates, before the auditor saw the surrogate list | 33 of 111 flags |
| False alarms on surrogates, after | 0 of 92 flags |
| Nameless identifying sentences flagged | 5 of 6 on set 1, 2 of 4 on set 2 |

How to read these numbers:
- **Zero is not proof.** 0 of 81 comes from four documents. The real miss rate is not zero.
- **The test is probably optimistic.** The same model family wrote the test documents and audited them. Real documents will be messier.
- **Over-redaction is high.** Public bodies, products and cities are replaced unless listed in `keep_public_entities`. That errs toward privacy but hurts readability, so tune the list for your documents.
- **Nameless-sentence counts are approximate.** The match compares phrases, so treat them as indicative.

## 3. Corrections to the Grok chat

### Errors and overstatements
| Grok said | What I found | Consequence |
|---|---|---|
| GLiNER2-PII has about 300M parameters and "strong span-level results" | The model card says 205M, its paper 0.3B, and another paper 287M. It ranked first on the SPY benchmark, but with F1 of 0.477 and precision of 0.35 to 0.37. It was trained only on synthetic data, and non-European locales are unmeasured | Useful, but not strong. It needs a filter for false positives |
| Protegrity-PII has "open weights" and is free | Hugging Face gates the model under a custom license tag, and I could not read the terms. Its 0.910 recall and 0.902 precision are on a benchmark its own authors propose | Do not list it as free open source without reading the license |
| Seeded generation makes mappings reproducible | Unkeyed seeding lets anyone test candidate names against the output | Seeds must come from a secret key. This tool uses a keyed hash |
| Restoring is "a simple reverse lookup" | Reverse lookup breaks when one surrogate contains another, when two originals share a form, and on spelling variants | This tool restores by stored position when text is unedited, and by reverse lookup otherwise |
| SurrogateShield shows surrogates beat placeholders | The 13.26-point BERTScore gain is real as reported. It comes from one author, on a 1,124-query synthetic corpus of short queries, not long documents | A promising signal, not evidence for long-form text |
| `leo-gan/pdf-anonymizer` | The repository does not resolve at that path | Removed |

### Dated
- Presidio's repository now resolves to `data-privacy-stack/presidio`. The latest release is 2.2.366, from 2026-10-27.
- OpenAI Privacy Filter got a passing mention. It is Apache-2.0, has a 128,000-token context, and is widely used. Its own README says it is "not an anonymization" tool, and it warns about under-detecting uncommon names and regional naming conventions.

### Omissions
- **Credentials.** API keys and passwords are absent from the chat, though they were part of your brief.
- **Threat model.** The chat frames risk around GDPR. For human-rights work the adversary may be a state with auxiliary data. Pseudonymization alone does not stop that adversary.
- **The session as a leak.** An agent that reads a raw file has already sent it to its provider. "Local only" must be enforced in the agent's tools.
- **Repeat mentions.** A long document mentions a person many ways. Missing this was the largest single cause of leaks in testing.
- **Surrogate safety.** A fake value can belong to a real person, so safe formats need reserved ranges.
- **Prompt injection.** A document under audit can contain instructions.
- **Your document types.** The chat ends with an unanswered line listing meeting notes, partner emails, transcriptions, status updates, reports and website text. Transcripts need spoken forms such as "jay dot osei at". Regex and NER missed these until I added rules.
- **Evaluation method.** The chat says to measure but not how. Tuning on your own test set misled me too: fixtures showed 0 leaks of 121 while the first blind set showed 59 of 194.

### Checks that held up
The hybrid detection advice, the case for surrogates over placeholders, the point that mapped data stays personal data, and the difficulty of differential privacy on free text are all reasonable. The Litvak and Jorge review exists (published 2026-08-16), but the publisher blocked access, so its contents are unverified.

## 4. Open-source landscape
Counts were read on 2026-11-04. They are snapshots: **I did not measure growth, so I cannot rank "fastest rising".**

| Resource | Role | License | Popularity | Note |
|---|---|---|---|---|
| Presidio | Detection framework | MIT | 11.7k stars | Default in Pass 2 |
| gitleaks | Secret scanning | MIT | 30.7k stars | Used in Pass 2 when installed |
| detect-secrets | Secret scanning library | Apache-2.0 | 4.7k stars | Used in Pass 2. Last PyPI release is May 2024 |
| TruffleHog | Secret scanning | AGPL-3.0 | 28.9k stars | Not used. It can verify credentials live against providers, which does not fit offline work |
| OpenAI Privacy Filter | PII model | Apache-2.0 | 2.8k stars, 106k downloads | Optional adapter, not run |
| GLiNER2-PII | PII model | Apache-2.0 | 157k downloads | Optional adapter, not run |
| NVIDIA NeMo Anonymizer | LLM-driven pipeline and agent skill | Apache-2.0 | 135 stars | Young, active, worth watching |
| SurrogateShield | LLM proxy with surrogates | Apache-2.0 | 169 stars | Closest published design |
| Phileas | Redaction engine | Apache-2.0 | 110 stars | Java, self-hosted |
| PrivAiTe, piighost, nullpii | Reversible LLM proxies | BSD-3, MIT, Apache-2.0 | 60, 18, 1 stars | For live LLM traffic, not documents |

### The two skills you pointed to
- **`glebis/session-anonymizer`** (157 installs, 408 repository stars, MIT). It is the closest design: three local layers of Natasha, OpenAI Privacy Filter and Ollama. Its guardrails are good, and I adopted "cloud verification only on already-anonymized text". Three things differ here. It pipes text already in context through its script, which is too late for privacy. It passes an encryption password on the command line. It also focuses on Russian therapy transcripts, and skills.sh shows a Snyk warning I did not investigate.
- **`hiyenwong/openai-privacy-filter`** (1 install, 3 stars). This is a methodology note for building such a model, not a tool. Use OpenAI's repository directly.

I read those skills' descriptions but did not audit their code, or that of the other projects listed.

## 5. What was built
| Pass | Default method | Configured by |
|---|---|---|
| 1. Patterns | Regex with checksums, your denylist, fuzzy matching with rapidfuzz, spoken numbers and emails | `pass1_patterns` |
| 2. Libraries | Presidio with spaCy `en_core_web_lg`, detect-secrets, gitleaks, credential rules, entropy | `pass2_libraries` |
| 3a. Local verify | Searches output for every original and re-runs detectors. No LLM | `pass3_agent_qa.deterministic_verify` |
| 3b. Agent audit | Fresh subagent reads anonymized text only and writes findings. Findings feed a re-run | `pass3_agent_qa.backend` |

Every pass can be removed in `pipeline.passes`, and each entity type has its own action: surrogate, generalize, redact or keep. Secrets are irreversible by default, and mappings use AES-256-GCM.

The design rationale, invariants and module contracts are in `spec/tech-spec.md`. Usage is in `README.md`.

**Statistical obfuscation is partial.** Dates shift by a keyed offset, and ages generalize to decades. There is no k-anonymity score and no differential privacy, because neither has a sound definition for free narrative text. Risky passages are flagged for a person to judge.

## 6. What was not verified
- **Live backends.** The Anthropic and Ollama backends ran only against fakes. Ollama cannot start here because its model folder is on an unmounted volume.
- **Optional models.** The GLiNER2 and OpenAI Privacy Filter adapters have never run, and the `opf` flags are guesses.
- **The full skill flow.** A fresh session found the skills and agent, and the guard blocked a raw file. I ran the CLI steps and auditors separately, with auditors following the agent file, but never ran `/anonymize` start to finish in a live session.
- **Real documents and other languages.** Everything tested is synthetic and in English.
- **Not addressed.** File metadata, PDF or Word input, and writing style (stylometry) are out of scope.

## 7. Decisions for you
1. **Which audit backend for your most sensitive documents?** The default sends pseudonymized text to Anthropic through Claude Code. Passes 1 and 2 leave about one value in eight in that text, so real values can reach the provider. For high-risk documents, use `ollama` once it is tested, or set the backend to `none` and rely on a person.
2. **Who signs off?** The gate fails until a person accepts flagged passages with `--human-reviewed`. In every audited document some judgment items remained, so expect to read them each time.

## Sources
- [Presidio](https://github.com/data-privacy-stack/presidio)
- [OpenAI Privacy Filter](https://github.com/openai/privacy-filter)
- [GLiNER2-PII model card](https://huggingface.co/fastino/gliner2-privacy-filter-PII-multi) and [paper](https://arxiv.org/abs/2605.09973)
- [Protegrity-PII report](https://arxiv.org/abs/2610.30518) and [model page](https://huggingface.co/Protegrity/protegrity-pii)
- [SurrogateShield](https://arxiv.org/abs/2606.29567)
- [Litvak and Jorge review](https://doi.org/10.1002/widm.70127)
- [session-anonymizer](https://www.skills.sh/glebis/claude-skills/session-anonymizer) and [openai-privacy-filter skill](https://www.skills.sh/hiyenwong/ai_collection/openai-privacy-filter)
- [NeMo Anonymizer](https://github.com/NVIDIA-NeMo/Anonymizer)
- [gitleaks](https://github.com/gitleaks/gitleaks), [TruffleHog](https://github.com/trufflesecurity/trufflehog), [detect-secrets](https://github.com/Yelp/detect-secrets)
