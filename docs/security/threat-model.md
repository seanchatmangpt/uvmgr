# Threat Model

## Assets

The primary assets are execution authority, source and lock integrity, developer credentials,
customer/cloud credentials delegated to invoked tools, release credentials, artifact identity,
and the integrity of execution receipts.

## Adversaries and failure modes

The model covers malicious dependencies, compromised CI actions, malicious or malformed CLI
input, accidental operator actuation, credential leakage, source/release substitution, poisoned
build images, and false-positive success caused by placeholders or non-failing verification.

## STRIDE analysis

| Threat | Example | Control |
|---|---|---|
| Spoofing | Publishing an image that is not the reviewed source | immutable source SHA + image digest receipt |
| Tampering | Mutable GitHub Action tag changes behavior after review | full commit-SHA action pins |
| Repudiation | A command reports success without executed evidence | execution receipts + fail-closed verification |
| Information disclosure | Secrets leak into source, logs, image, or receipts | no repository secrets; delegated runtime credentials |
| Denial of service | Unbounded subprocess or CI execution | bounded command/runtime interfaces and workflow timeouts |
| Elevation of privilege | Build toolchain or root runtime increases attack surface | multi-stage image + non-root runtime UID |
| Supply-chain substitution | Dependency or build artifact changes between validation and publication | frozen lock, audit-before-release, immutable digest |
| Governance bypass | Manual workflow publishes directly to production | production admitted only from semantic-version tags |

## Primary trust-boundary controls

### Commands → Ops → Runtime

Runtime is the side-effect boundary. Command modules should not bypass it for subprocess,
filesystem, cloud, Git, or deployment actuation. New features must provide typed refusal when
the required runtime implementation is not admitted.

### CI → repository

Pull-request CI has `contents: read`, disables persisted checkout credentials, and is forbidden
from repair/push behavior. Third-party Actions are pinned by commit SHA and checked by the
enterprise verifier.

### Build → runtime container

Compilers and package-install tooling are confined to the build stage. The runtime stage receives
only the installed environment, executes as UID/GID `10001`, and is tested to ensure `sudo`,
`gcc`, and `g++` are absent.

### Release → registry

Only the publication job receives `packages: write`. A tag-triggered release maps to the
`production` GitHub Environment; manual dispatch is limited to non-production channels.
Published images include SHA tags, BuildKit SBOM/provenance attestations, and a digest receipt.

## Residual and external risks

The repository cannot prove organization-level branch protection, GitHub Environment approval
rules, secret-scanning configuration, SSO enforcement, registry retention/immutability, incident
routing, or customer contractual controls. Those remain `REQUIRED_EXTERNAL`, not `ALIVE`.

Dependency audit also detects only vulnerabilities present in its current advisory sources; it is
not a proof of absence of unknown vulnerabilities.
