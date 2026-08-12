# Enterprise Support Matrix

## Runtime admission

`uvmgr` uses an explicit certified runtime envelope. A version outside this envelope is not
best-effort enterprise support; it is outside the admitted platform boundary until the lock,
source syntax, behavioral smoke tests, and package manufacture all pass on that runtime.

| Runtime | Standing | Admission evidence |
|---|---|---|
| CPython 3.12.x | Admitted / canonical | CI canonical rail; pinned runner interpreter 3.12.13 |
| CPython 3.13.x | Admitted / compatibility | CI compatibility rail; pinned runner interpreter 3.13.14 |
| CPython <=3.11 | REFUSED | outside `requires-python`; source uses syntax not certified below 3.12 |
| CPython >=3.14 | REFUSED | outside `requires-python`; current locked native dependency chain is not certified there |
| PyPy / GraalPy / free-threaded CPython | REFUSED | no exact-subject CI or package evidence |

The package and lock contracts encode the same interval: `>=3.12,<3.14`.

## Delivery units

| Unit | Enterprise standing boundary |
|---|---|
| Source checkout | exact Git subject + frozen lock + repository contract + tests |
| PyInstaller executable | Linux-hosted build and fail-closed dogfood verification |
| OCI runtime image | Linux amd64/arm64 release build; non-root runtime; SBOM/provenance on publication |
| PyPI distribution | build capability exists; public publication is not asserted until a tagged release is executed |

## Operating-system support

The enterprise CI/release boundary is Linux-first. macOS and Windows source execution may work,
but are not advertised as certified until dedicated exact-subject rails execute the same contract
and behavioral suites. This distinction prevents package portability from being mistaken for an
operational support commitment.

## Toolchain

Canonical validation and release pin:

- CPython `3.12.13`;
- compatibility CPython `3.13.14`;
- `uv` `0.12.3`;
- third-party GitHub Actions by full commit SHA.

Base OCI images are resolved and recorded by BuildKit provenance at manufacture time. If a customer
requires fully hermetic rebuilds from a fixed base image digest, that digest must be pinned as part
of the customer release policy rather than inferred from a mutable tag.
