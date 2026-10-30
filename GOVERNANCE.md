# Governance

Water Ledger is maintained by Northline Hydrology. This document sets out how decisions are made so that more people can
take part as the project grows.

## Roles

- **Users** use the packages and data, and report problems.
- **Contributors** have had a pull request merged.
- **Reviewers** are contributors trusted to review changes in an area (a state's data, a model). They are added by the
  maintainers.
- **Maintainers** merge changes, publish releases and snapshots, and keep this document.

Current maintainers:

| Name | Affiliation | GitHub |
|---|---|---|
| Andrew Sommerlot | Northline Hydrology | [@drmerlot](https://github.com/drmerlot) |

## How decisions are made

- **Routine changes** (fixes, tests, documentation) are merged after one maintainer or reviewer approves.
- **Changes to the numbers** (equations, parameter ranges, data sources, assumptions) need an issue describing the change,
  its source and its effect on published estimates, and approval from a maintainer. They raise `MODEL_VERSION` and are
  recorded in the methods changelog.
- **Significant changes** (new API, new data release format, a new state's rules, anything breaking) start as a short
  design note in [docs/design](docs/design/), numbered in order, open for comment for at least one week once the
  project has more than one maintainer. A design note is marked *agreed* when accepted, and is not edited afterward
  except to note what superseded it.
- Decisions aim for consensus. When it can't be reached, the maintainers decide and record the reason in the issue or
  design note.

## Releases and data

- Package releases follow semantic versioning and are published to PyPI from a tagged commit by trusted publishing.
- The README is updated before every release, in the commit that is tagged or an earlier one: what the packages do, the
  states, and the version numbers it states. `tests/test_readme.py` checks the version numbers.
- A state snapshot is published only after it passes its statewide checks; its manifest records the checks, sources,
  package versions and model version.
- Published snapshots are not changed in place except to republish the same date with a fix, recorded in the build
  history.

## Conflicts of interest

Reviewers and maintainers say when they have a financial or professional interest in a change, such as work for a party
to a proposal the change would affect, and do not approve such changes themselves.

## Changes to this document

Changes to governance follow the process for significant changes.
