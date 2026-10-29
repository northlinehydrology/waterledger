# Contributing

Water Ledger estimates are used in public decisions about water supply and streams, so contributions are held to the
standards that apply to environmental models used in public decisions. We follow, as far as a small open project can:

- EPA's [Guidance on the Development, Evaluation, and Application of Environmental Models](https://www.epa.gov/sites/default/files/2015-04/documents/cred_guidance_0309.pdf)
  (Council for Regulatory Environmental Modeling, EPA/100/K-09/003, 2009): documented assumptions, evaluation against
  observations, sensitivity and uncertainty analysis, and transparency about limits.
- OMB's [Information Quality Act guidelines](https://www.govinfo.gov/content/pkg/FR-2002-02-22/pdf/R2-59.pdf)
  (67 FR 8452, 2002) and [M-19-15](https://www.whitehouse.gov/wp-content/uploads/2019/04/M-19-15.pdf) (2019):
  objectivity (accurate, sourced, reproducible), utility and integrity of published information, and a way for the
  public to request corrections.
- OMB's [Federal Source Code Policy](https://trumpwhitehouse.archives.gov/sites/whitehouse.gov/files/omb/memoranda/2016/m_16_21.pdf)
  (M-16-21, 2016), in its principle of working in the open: code, methods and data releases are public, and changes are
  reviewed in public.

## Ways to contribute

- **Report a problem with a number or a dataset**: use the *Data or estimate problem* issue form. Say which place, what
  Water Ledger shows, what you believe is correct, and your source. This is the project's request-for-correction process.
- **Report a bug**: use the *Bug report* form, with the version (`python -c "import waterledger; print(waterledger.__version__)"`)
  and a minimal example.
- **Propose a method change or a new state**: open an issue first. Larger changes get a short design note in
  [docs/design](docs/design/) before code (see [GOVERNANCE.md](GOVERNANCE.md)).
- **Pull requests**: welcome for fixes, tests, documentation and agreed changes.

## Rules for changes

1. **Sources.** Every number, parameter range and dataset cites a public source, or is labeled as an estimate. A range
   that stands in for a facility's own data is marked **[A]** in the code comment and the methods.
2. **Public data only.** Nothing from a private engagement, a confidential filing or a non-public utility record goes into
   the packages or the published snapshots.
3. **Numbers change deliberately.** Any change to model results fails the golden test until `MODEL_VERSION` is raised, the
   change is listed in the methods changelog with its reason, and the reproduction test is updated. Code-only changes
   leave `MODEL_VERSION` alone.
4. **Tests.** New behavior comes with tests. Tests that reach the network are marked `live`; tests that need a state's
   data are marked with that state (`state_oh` and so on).
5. **Changelog.** User-visible changes get a line in [CHANGELOG.md](CHANGELOG.md). Breaking changes are labeled and go in
   a major release.
6. **Commits.** One logical change per commit, with a message that says what changed and why.
7. **Scope.** Water Ledger produces planning-level screening estimates. Contributions should not present results as
   engineering design or as a substitute for a facility's data, a utility's analysis or a permit review.

## Setup

```bash
uv sync                      # all three packages, editable, with dev tools
uvx ruff check .             # lint
uv run pytest                # unit tests, golden test
uv run pytest -m live        # data sources still answer (network)
```

## License

Contributions are accepted under the repository's [BSD 3-Clause License](LICENSE). By opening a pull request you agree
that your contribution may be distributed under it.
