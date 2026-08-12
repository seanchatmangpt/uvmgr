"""Tests for the repository-observable enterprise contract."""

from pathlib import Path

from uvmgr.core import enterprise_contract


def _repo_root() -> Path:
    """Return the repository root for contract verification."""
    return Path(__file__).resolve().parents[1]


def test_enterprise_contract_verifies_repository() -> None:
    """Require the checkout to satisfy all locally provable controls."""
    assert enterprise_contract.verify_repository(_repo_root()) == ()


def test_mutable_action_reference_is_rejected(tmp_path: Path) -> None:
    """Reject mutable GitHub Action tags at the workflow boundary."""
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


def test_immutable_action_reference_is_admitted(tmp_path: Path) -> None:
    """Admit a workflow action only when the ref is a full commit SHA."""
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text(
        "steps:\n"
        "  - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803\n",
        encoding="utf-8",
    )

    assert enterprise_contract._verify_action_pins(tmp_path) == []


def test_ci_synthetic_merge_checkout_is_rejected(tmp_path: Path) -> None:
    """Reject PR CI that labels a default merge-ref checkout as the exact subject."""
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text(
        "env:\n"
        "  SUBJECT_SHA: ${{ github.event.pull_request.head.sha || github.sha }}\n"
        "steps:\n"
        "  - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803\n",
        encoding="utf-8",
    )

    errors = enterprise_contract._verify_ci_exact_subject(tmp_path)

    assert any("every checkout must bind SUBJECT_SHA" in error for error in errors)


def test_ci_exact_subject_binding_is_admitted(tmp_path: Path) -> None:
    """Admit CI only when checkout, execution identity, and artifacts share one subject."""
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text(
        "env:\n"
        "  SUBJECT_SHA: ${{ github.event.pull_request.head.sha || github.sha }}\n"
        "steps:\n"
        "  - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803\n"
        "    with:\n"
        "      ref: ${{ env.SUBJECT_SHA }}\n"
        "  - run: test \"$(git rev-parse HEAD)\" = \"${SUBJECT_SHA}\"\n"
        "  - run: printf '%s\\n' \"${SUBJECT_SHA}\" | tee receipts/subject.sha\n"
        "  - name: enterprise-validation-${{ env.SUBJECT_SHA }}\n"
        "  - name: uvmgr-dogfood-${{ env.SUBJECT_SHA }}\n",
        encoding="utf-8",
    )

    assert enterprise_contract._verify_ci_exact_subject(tmp_path) == []


def test_runtime_section_rejects_build_toolchain(tmp_path: Path) -> None:
    """Reject build-time package installation from the runtime image section."""
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