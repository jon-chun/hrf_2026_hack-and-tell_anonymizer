# anon3pass

Replaces names, contacts, IDs and credentials in long documents with realistic stand-ins that can be restored later, in three configurable passes.

The output is pseudonymized, not anonymous. Read `report/summary-report.md` before relying on it, especially sections 2 and 7.

## Contents
| Path | What it is |
|---|---|
| `report/summary-report.md` | Critique of the Grok chat, tool landscape, measured results |
| `spec/tech-spec.md` | Threat model, invariants, module contracts |
| `engine/config.yaml` | Every pass, threshold and entity policy |
| `.claude/skills/` | `anonymize`, `anon-qa`, `anon-restore` |
| `.claude/agents/anon-leak-auditor.md` | The Pass 3 auditor |
| `.claude/hooks/guard_raw.py` | Blocks agent access to raw files, maps and keys. Best effort, not a sandbox |
| `bin/anon` | The command-line tool |

## Setup
```bash
cd anon-artifacts/engine && uv sync && cd ..
bin/anon init-key
cp terms.local.yaml.example terms.local.yaml   # add your own organization and project names
```
The key is stored at `~/.config/anon3pass/master.key`. Back it up safely: without it, documents cannot be restored.

## Use it from Claude Code
Start Claude Code inside `anon-artifacts/` so the skills, agent and guard load. Save files yourself into `workspace/raw/`, then ask:
```
/anonymize workspace/raw/notes.md
```
Do not paste sensitive text into the chat, because it reaches the model provider immediately.

## Use it from the shell
```bash
bin/anon run workspace/raw/notes.md -o workspace/out
bin/anon verify workspace/out/notes.anon.md --map workspace/out/notes.map.enc
bin/anon qa-packet workspace/out/notes.anon.md -o workspace/out/notes.qa_packet.json
bin/anon qa-run workspace/out/notes.qa_packet.json -o workspace/out/notes.findings.json
bin/anon qa-apply workspace/out/notes.findings.json --map workspace/out/notes.map.enc -o workspace/out/notes.extra_terms.yaml
bin/anon run workspace/raw/notes.md -o workspace/out --extra-terms workspace/out/notes.extra_terms.yaml
bin/anon gate workspace/out/notes.report.json --findings workspace/out/notes.findings.json
bin/anon restore workspace/out/notes.anon.md --map workspace/out/notes.map.enc -o restored.md
```
With the default `claude_code` backend, `qa-run` only reports that an agent must be dispatched, so use the skill. Re-run `verify` and the audit after each `run`. The gate fails until a person has read flagged passages and adds `--human-reviewed`.

## Configure the passes
```yaml
pipeline:
  passes: [patterns, libraries, agent_qa]   # remove any pass
pass2_libraries:
  ner: {engine: presidio_spacy}             # gliner2 | opf | none; those adapters are untested
pass3_agent_qa:
  backend: claude_code                      # anthropic | ollama | none; live calls are untested
entity_policy:
  ORGANIZATION: keep                        # surrogate | generalize | redact | keep
```

## Test
```bash
cd engine
uv run --group dev python -m pytest tests -q
PYTHONPATH=src uv run python eval/run_eval.py --configs pass1,pass2,pass1+2,pass1+2-noterms
```
`eval/heldout` and `eval/heldout2` were written without sight of the code. Do not tune rules on `heldout2` if you want its score to stay meaningful.

## Commit note
Test files hold deliberately fake credentials, which secret scanners flag. Allowlist those exact false positives rather than skipping the hook. `workspace/`, keys, maps and `terms.local.yaml` are gitignored.
