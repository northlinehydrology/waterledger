# Security Policy

This policy follows the structure of the [CISA vulnerability disclosure policy template](https://www.cisa.gov/vulnerability-disclosure-policy-template)
used by federal agencies.

## Supported versions

| Version | Supported |
|---|---|
| 3.x | Yes |
| 2.x and earlier | No; upgrade to 3.x |

## Scope

- The `waterledger`, `waterledger-data` and `waterledger-models` packages in this repository.
- The published state snapshots at data.waterledger.org, including their integrity (the package checks every file
  against the manifest's SHA-256 checksums before use).

Out of scope: the public data sources the packages read (report those to the agency that publishes them), denial of
service, and social engineering.

## Reporting a vulnerability

Report privately through GitHub's
[private vulnerability reporting](https://github.com/northlinehydrology/waterledger/security/advisories/new). Do not open
a public issue. Include what is affected, steps to reproduce, and the impact you expect.

We will acknowledge a report within 5 business days, keep you informed while we fix it, and credit you in the advisory
unless you prefer otherwise.

## Safe harbor

Research done in good faith and consistent with this policy is authorized; we will not pursue or support legal action
over it. Avoid privacy violations, data destruction and service disruption, and give us reasonable time to fix an issue
before disclosing it.

## Data integrity

Water Ledger publishes estimates used in public decisions. A snapshot that does not match its manifest, or a published
number that appears to have been altered, is treated as a security issue. Report it the same way.
