"""Tests for the repository-observable enterprise contract."""

from pathlib import Path

from uvmgr.core import enterprise_contract


def _repo_root() -> Path:
    """Return the repository root for contract verification."""

    return Path(__file__).resolve().parents[1]


def test_enterprise_contract_verifies_repository() -> None:
    """The checked-in repository must satisfy all locally provable controls."""

    assert enterprise_contract.verify_repository(_repo_root()) == ()


def test_mutable_action_reference_is_rejected(tmp_path: Path) -> None:
    """Mutable GitHub Action tags must not satisfy enterprise supply-chain policy."""

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text(
        "steps:\n  - uses: actions/checkout@v6\n",
        encoding="utf-8",
    )

    errors = enterprise_contract._verify_action_pins(tmp_path)

    assert errors == [
        "EA-ACTION-PIN: .github/workflows/ci.yml: actions/checkout@v6 is mutable"
    ]


def test_runtime_section_rejects_build_toolchain(tmp_path: Path) -> None:
    """Runtime images must remain free of build-time package installation."""

    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text(
        "FROM python:3.12 AS build\n"
        "RUN echo build\n"
        "FROM python:3.12-slim AS app\n"
        "RUN apt-get update && apt-get install -y build-essential\n",
        encoding="utf-8",
    )
    policy = {
        "section_controls": [
            {
                "id": "EA-CTR-002",
                "path": "Dockerfile",
                "start": "FROM python:3.12-slim AS app",
                "required": [],
                "forbidden": ["apt-get", "build-essential"],
            }
        ]
    }

    errors = enterprise_contract._verify_section_controls(tmp_path, policy)

    assert errors == [
        "EA-CTR-002: Dockerfile section contains forbidden: apt-get",
        "EA-CTR-002: Dockerfile section contains forbidden: build-essential",
    ]
