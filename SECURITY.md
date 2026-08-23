# Security Policy

## Supported security boundary

`uvmgr` is a local development-workflow CLI. The security boundary includes command
admission, subprocess execution, filesystem effects, dependency resolution, package and
container manufacture, release publication, credential handling delegated to external
providers, and the integrity of execution receipts.

The repository does not claim a public support SLA. Enterprise response, remediation,
indemnity, and disclosure timelines must be established in the customer agreement rather
than inferred from this public repository.

## Reporting a vulnerability

Do **not** disclose a suspected vulnerability in a public issue.

Use GitHub's private security-advisory workflow when it is enabled for this repository.
If private advisory submission is unavailable, contact `info@chatmangpt.com` with:

- the affected commit, tag, package, or image digest;
- a minimal reproduction;
- observed impact and required preconditions;
- whether credentials, tokens, customer data, or release authority may be exposed.

Do not include live credentials or customer-confidential data in the report.

## Security invariants

The repository is designed around the following invariants:

1. Third-party GitHub Actions are pinned to immutable commit SHAs.
2. Pull-request CI has read-only repository permission and does not repair or push source.
3. Production container publication is admitted only from a semantic-version tag.
4. Locked dependencies are audited before publication.
5. Published container images include BuildKit provenance and SBOM attestations.
6. Runtime containers execute as a non-root UID and do not contain the build toolchain.
7. Capability presence is not execution authority; excluded command families remain typed refusals.
8. External controls such as branch protection and production approvers are not reported as
   satisfied by repository-local verification.

Run the locally provable security/governance checks with:

```bash
uv run python -m uvmgr.core.enterprise_contract
uv run uvmgr capabilities verify
```

## Secrets and credentials

No production secret belongs in the repository, test fixtures, build context, image layers,
execution receipts, or GitHub Actions logs. Runtime credentials should come from the
platform-native credential provider or the execution environment and should be scoped to
the minimum authority required for the invoked operation.
