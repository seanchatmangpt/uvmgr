# Release, Rollback, and Recovery

## Release authority

Validation and publication are separate rails.

- `CI` is reversible and non-publishing.
- `Release` performs publication.
- A semantic-version tag is the only repository-defined path to the `production` environment.
- Manual dispatch can publish only to `development`, `test`, or `acceptance`.
- Only the release container job receives `packages: write`.

The production GitHub Environment should be configured outside the repository with required
approvers and deployment protection rules.

## Release protocol

1. Merge only a reviewed exact head whose required checks are successful.
2. Create an annotated or lightweight semantic-version tag `vMAJOR.MINOR.PATCH` at that exact commit.
3. Release verification re-checks the frozen lock, enterprise repository contract, and dependency audit.
4. Buildx produces `linux/amd64` and `linux/arm64` images from that tag.
5. Publish immutable SHA and semantic-version tags with SBOM and provenance attestations.
6. Persist a release receipt containing source SHA, source ref, environment, image digest, and receipt manifest.
7. Promote customer documentation by immutable image digest, not by a mutable environment tag alone.

## Rollback

Rollback is artifact selection, not source mutation.

1. Identify the last admitted image digest from a release receipt.
2. Deploy or pull the exact digest:
   `ghcr.io/seanchatmangpt/uvmgr@sha256:<digest>`.
3. Preserve the failed digest and incident evidence; do not overwrite it.
4. Repair forward on a new commit/tag.
5. Re-run the full release verification before republishing.

A rollback that cannot identify the exact prior digest is `BLOCKED` because artifact identity is
part of the recovery contract.

## Recovery model

`uvmgr` is stateless; customer state lives in repositories, package registries, external tools,
cloud platforms, and credential providers. Disaster recovery therefore focuses on reconstructing
a trusted executable from immutable source/lock state and recovering the corresponding receipts.

Required enterprise platform controls:

- protected and recoverable source repository;
- immutable/retained release artifacts and receipts;
- registry retention and deletion protection appropriate to customer policy;
- production environment approvals;
- incident owner and escalation route;
- credential revocation and rotation procedures.

Numerical RTO/RPO and support-response commitments are deliberately not fabricated in this
repository. They must be measured and contracted for the customer's operating environment.
