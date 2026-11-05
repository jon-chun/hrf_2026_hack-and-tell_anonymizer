---
name: anon-restore
description: Restore an anonymized document to its original values with the anon3pass vault. Use when the user says "restore", "de-anonymize", "put the real names back", "reverse the anonymization", or gives an .anon file plus its map.
argument-hint: <doc.anon.ext> --map <doc.map.enc> -o <output path>
allowed-tools: Bash(bin/anon restore *)
---

# Restore an anonymized document

## Hard rules
- The restored file contains REAL personal data. Warn the user before running and after it finishes, in one line each.
- NEVER Read, cat or print the restored file, the map (`*.map.enc`), a key or `terms.local.yaml`. Never show restored text in chat. Only the CLI handles them.
- Write only to the output path the user names. If none is given, ask for one; do not choose a path inside a shared or synced folder.
- Do not overwrite an existing file. If the path exists, ask the user for another path.

## Steps
Assume cwd is `anon-artifacts/`.

1. Confirm the three paths: the anonymized file, its map `<doc>.map.enc` in the same output folder, and the destination.
2. Warn: "The restored file will contain real names and identifiers; handle it as sensitive."
3. Run: `bin/anon restore <doc.anon.ext> --map <doc.map.enc> -o <destination>`.
4. Report from the CLI's counts only: mode (exact or reverse lookup), replacements restored, unmatched surrogates, secrets left as placeholders (secrets are irreversible by default).
5. Exit codes: 3 means the map does not match or restoring failed; 4 means a missing key or dependency. Report the code and the message, nothing else.

## Notes
- An unedited anonymized file restores byte for byte. If it was edited, restoring uses reverse lookup and can miss text that was changed; the unmatched count says how many surrogates it could not place.
- Restored files should not be passed to any model. Do not offer to summarize or review them.
