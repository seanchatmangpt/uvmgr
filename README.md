# uvmgr

[![License](https://img.shields.io/github/license/seanchatmangpt/uvmgr.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/seanchatmangpt/uvmgr/ci.yml)](https://github.com/seanchatmangpt/uvmgr/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12--3.13-blue.svg)](https://www.python.org/)

`uvmgr` is a Python development-workflow CLI built around `uv`. It provides dependency, test, build, lint, automation, observability, workspace, infrastructure, and related development capabilities behind an explicit command-admission boundary.

The repository is **source-first**. Tagged release publication is a separate actuation; the development branch should be validated and run from an exact checkout.

## Quick start

```bash
git clone https://github.com/seanchatmangpt/uvmgr.git
cd uvmgr

uv sync --frozen --all-extras --group dev --group ci
uv run uvmgr --version
uv run uvmgr --help
```

A few common operations:

```bash
# Dependencies
uv run uvmgr deps list
uv run uvmgr deps add requests

# Tests
uv run uvmgr tests run --no-parallel --no-coverage

# Linting
uv run uvmgr lint check

# Build distributions
uv run uvmgr build dist

# Build and verify the standalone uvmgr executable
uv run uvmgr build dogfood --test --no-platform
```

## Capability standing

`uvmgr` does not treat the presence of a Python file as execution authority. The command registry explicitly admits or excludes command surfaces, and the capability ledger keeps structural observation separate from execution.

```bash
# Inspect command standing
uv run uvmgr capabilities list

# Fail if an admitted command is structurally broken or unsupported
uv run uvmgr capabilities verify
```

The standing vocabulary includes:

- `ALIVE` — exact behavior has executed successfully against the admitted subject.
- `PARTIAL_ALIVE` — a structural or bounded boundary is valid, but the exact behavior has not been executed.
- `BUILD_BROKEN` — an admitted surface cannot be constructed or imported.
- `UNSUPPORTED` — required implementation is absent.
- `REFUSED:EXCLUDED_BY_REGISTRY` — source may exist, but the registry intentionally withholds execution authority.

Inspection is not execution. `capabilities verify` proves structural admission; behavioral commands and CI provide execution evidence.

## Certified runtime envelope

The supported Python runtime is intentionally bounded to **3.12.x–3.13.x**. Packaging metadata,
the lockfile, and CI encode the same envelope (`>=3.12,<3.14`). Python 3.11 is outside the
certified source-syntax boundary, and Python 3.14 is refused until the locked native dependency
chain supports it. Unsupported runtimes are not treated as best-effort enterprise support.

Canonical CI executes Python 3.12.13 and a Python 3.13.14 compatibility rail using the same
frozen lock. The `uv` toolchain itself is pinned to 0.12.3 in validation and release workflows.

## Architecture

The primary execution path is:

```text
CLI command
    ↓
Command layer        src/uvmgr/commands/
    ↓
Operations layer     src/uvmgr/ops/
    ↓
Runtime layer        src/uvmgr/runtime/
    ↓
External process / filesystem / tool boundary
    ↓
Execution receipt / observed consequence
```

The separation is deliberate:

- **Commands** parse user intent and render results.
- **Ops** construct deterministic plans and domain decisions.
- **Runtime** owns subprocess execution, filesystem effects, and other external actuation.
- **Core** contains shared instrumentation, configuration, process, capability, and support primitives.

New command surfaces should preserve this layering rather than adding ambient execution to the command layer.

## Enterprise control plane

Repository-observable enterprise controls are declared in `enterprise/controls.json` and are
verified by code rather than prose:

```bash
uv run python -m uvmgr.core.enterprise_contract
```

The verifier checks required governance artifacts, immutable GitHub Action pins, non-mutating CI,
release admission semantics, and the hardened runtime-container boundary. Organization-level
controls such as branch protection and production approvers remain explicit external controls and
are not promoted to `ALIVE` by repository-local inspection.

Production release is separated from pull-request validation. A semantic-version tag enters the
production GitHub Environment; manual publication is restricted to non-production channels.
Published OCI images are multi-architecture and include SBOM/provenance attestations plus an
immutable digest receipt.

## Testing and replay

The test command forwards pytest-owned selectors and flags through a receipted Command → Ops → Runtime path.

```bash
# Normal execution
uv run uvmgr tests run tests/test_cli.py -v --tb=short --no-parallel --no-coverage

# Local CI capability
uv run uvmgr tests ci verify --skip-build
```

Execution receipts are written under `reports/receipts/`. They bind the executed argv, process result, and receipt digest so a successful test invocation can be distinguished from test discovery or configuration inspection.

The canonical pull-request CI checks the frozen lock, compilation, immutable workflow dependencies,
the enterprise contract, a bounded non-mutating Ruff surface, behavioral tests, the certified Python 3.12–3.13
compatibility envelope, `uvmgr` replay, capability admission, a hardened non-root container, and a standalone
PyInstaller dogfood executable.

## Standalone executable

`uvmgr build dogfood` manufactures a standalone executable with PyInstaller and tests the artifact before accepting it.

```bash
uv run uvmgr build dogfood --test --no-platform
```

The frozen import graph is projected from the same admitted command registry used by the source CLI. Dogfood verification checks root construction, every admitted command's help route, typed incomplete-standing markers, and frozen capability verification. A failed self-test exits non-zero.

## Development

Install the exact locked development environment:

```bash
uv sync --frozen --all-extras --group dev --group ci
```

Useful narrow gates:

```bash
uv lock --check
uv run python -m compileall -q src/uvmgr
uv run python -m uvmgr.core.enterprise_contract
uv run pytest tests/test_build_exe.py -v --tb=short
uv run uvmgr capabilities verify
```

Before adding a command:

1. Add the Typer command surface under `src/uvmgr/commands/`.
2. Add Ops and Runtime boundaries when the capability actuates external state.
3. Admit the command through the canonical command registry.
4. Add tests for planning, execution/refusal, and CLI construction.
5. Verify the source path and the frozen executable path when packaging behavior changes.

## Documentation

- [Enterprise architecture](docs/architecture/enterprise-architecture.md)
- [Threat model](docs/security/threat-model.md)
- [Release, rollback, and recovery](docs/operations/release-and-recovery.md)
- [Security policy](SECURITY.md)
- [Architecture and contributor doctrine](CLAUDE.md)
- [Tutorials](docs/tutorials/)
- [How-to guides](docs/how-to/)
- [Explanations](docs/explanation/)
- [Reference](docs/reference/)

Documentation is descriptive; executable standing comes from the registry, tests, receipts, enterprise contract, and exact-subject CI.

## License

MIT. See [LICENSE](LICENSE).
