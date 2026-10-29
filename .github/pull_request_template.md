## What this changes

<!-- What changed and why. Link the issue or design note. -->

## Checklist

- [ ] Tests added or updated; `uv run pytest` and `uvx ruff check .` pass
- [ ] User-visible change listed in CHANGELOG.md
- [ ] Every new number, range or dataset cites a public source or is labeled as an estimate ([A] where it stands in for a facility's data)
- [ ] Public data only: nothing from private engagements or non-public records
- [ ] If model results change: `MODEL_VERSION` raised, methods changelog entry written, golden and reproduction tests updated
- [ ] If the snapshot format or a state's data changes: snapshot rebuilt and checked (`waterledger check-snapshot`)
- [ ] Docs updated (README, methods notes, design note) where needed
