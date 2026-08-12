"""Executable repository governance for the enterprise delivery boundary.

This module validates only controls that can be observed from the repository
checkout. Platform controls such as branch protection and environment approvals
remain explicitly external and must not be promoted to ALIVE by this verifier.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_ACTION_RE = re.compile(r"^\s*-\s*uses:\s*([^@\s]+)@([^\s#]+)", re.MULTILINE)
_FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_CI_SUBJECT_EXPRESSION = "SUBJECT_SHA: ${{ github.event.pull_request.head.sha || github.sha }}"
_CI_SUBJECT_REF = "ref: ${{ env.SUBJECT_SHA }}"


def _read_text(root: Path, relative_path: str) -> str:
    """Read a repository file using UTF-8."""
    return (root / relative_path).read_text(encoding="utf-8")


def _load_policy(root: Path) -> dict[str, Any]:
    """Load the machine-readable enterprise control contract."""
    policy_path = root / "enterprise" / "controls.json"
    return json.loads(policy_path.read_text(encoding="utf-8"))


def _verify_required_files(root: Path, policy: dict[str, Any]) -> list[str]:
    """Return missing required-file failures."""
    return [
        f"EA-FILE: missing required file: {relative_path}"
        for relative_path in policy["required_files"]
        if not (root / relative_path).is_file()
    ]


def _verify_action_pins(root: Path) -> list[str]:
    """Require every third-party GitHub Action to use an immutable commit SHA."""
    errors: list[str] = []
    workflow_dir = root / ".github" / "workflows"
    workflow_paths = sorted(
        [*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")],
        key=lambda path: path.as_posix(),
    )
    for workflow_path in workflow_paths:
        text = workflow_path.read_text(encoding="utf-8")
        relative = workflow_path.relative_to(root).as_posix()
        errors.extend(
            f"EA-ACTION-PIN: {relative}: {action}@{ref} is mutable"
            for action, ref in _ACTION_RE.findall(text)
            if not action.startswith("./") and not _FULL_SHA_RE.fullmatch(ref)
        )
    return errors


def _verify_ci_exact_subject(root: Path) -> list[str]:
    """Require every CI checkout and receipt to bind the exact triggering subject."""
    path = root / ".github" / "workflows" / "ci.yml"
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    if _CI_SUBJECT_EXPRESSION not in text:
        errors.append("EA-CI-SUBJECT: CI does not derive an explicit exact subject SHA")

    checkout_count = text.count("uses: actions/checkout@")
    subject_ref_count = text.count(_CI_SUBJECT_REF)
    if checkout_count != subject_ref_count:
        errors.append(
            "EA-CI-SUBJECT: every checkout must bind SUBJECT_SHA "
            f"(checkouts={checkout_count}, bound={subject_ref_count})"
        )

    if "${GITHUB_SHA}" in text:
        errors.append("EA-CI-SUBJECT: CI artifact execution still references synthetic GITHUB_SHA")

    if text.count("github.sha") != 1:
        errors.append(
            "EA-CI-SUBJECT: github.sha may appear only as the non-PR fallback in SUBJECT_SHA"
        )

    required_receipt_fragments = (
        'test "$(git rev-parse HEAD)" = "${SUBJECT_SHA}"',
        "enterprise-validation-${{ env.SUBJECT_SHA }}",
        "uvmgr-dogfood-${{ env.SUBJECT_SHA }}",
        'printf \'%s\\n\' "${SUBJECT_SHA}" | tee receipts/subject.sha',
    )
    errors.extend(
        f"EA-CI-SUBJECT: CI missing exact-subject receipt fragment: {fragment}"
        for fragment in required_receipt_fragments
        if fragment not in text
    )
    return errors


def _verify_text_controls(root: Path, policy: dict[str, Any]) -> list[str]:
    """Evaluate declarative whole-file text controls."""
    errors: list[str] = []
    for control in policy["text_controls"]:
        text = _read_text(root, control["path"])
        errors.extend(
            f"{control['id']}: {control['path']} missing required fragment: {fragment}"
            for fragment in control.get("required", [])
            if fragment not in text
        )
        errors.extend(
            f"{control['id']}: {control['path']} contains forbidden fragment: {fragment}"
            for fragment in control.get("forbidden", [])
            if fragment in text
        )
    return errors


def _section(text: str, start: str) -> str | None:
    """Return the Dockerfile-like section beginning at start."""
    index = text.find(start)
    if index < 0:
        return None
    section = text[index:]
    next_from = section.find("\nFROM ", len(start))
    if next_from >= 0:
        return section[:next_from]
    return section


def _verify_section_controls(root: Path, policy: dict[str, Any]) -> list[str]:
    """Evaluate controls scoped to one declarative file section."""
    errors: list[str] = []
    for control in policy["section_controls"]:
        text = _read_text(root, control["path"])
        section = _section(text, control["start"])
        if section is None:
            errors.append(
                f"{control['id']}: {control['path']} missing section: {control['start']}"
            )
            continue
        errors.extend(
            f"{control['id']}: {control['path']} section missing: {fragment}"
            for fragment in control.get("required", [])
            if fragment not in section
        )
        errors.extend(
            f"{control['id']}: {control['path']} section contains forbidden: {fragment}"
            for fragment in control.get("forbidden", [])
            if fragment in section
        )
    return errors


def verify_repository(root: Path) -> tuple[str, ...]:
    """Verify repository-observable enterprise controls.

    Returns
    -------
    tuple[str, ...]
        Empty when every locally provable control is satisfied.
    """
    root = root.resolve()
    policy = _load_policy(root)
    errors = [
        *_verify_required_files(root, policy),
        *_verify_action_pins(root),
        *_verify_ci_exact_subject(root),
        *_verify_text_controls(root, policy),
        *_verify_section_controls(root, policy),
    ]
    return tuple(errors)


def main() -> int:
    """Run the enterprise verifier against the current checkout."""
    root = Path.cwd()
    errors = verify_repository(root)
    if errors:
        print("BUILD_BROKEN: enterprise contract verification failed")
        for error in errors:
            print(f"- {error}")
        return 1

    policy = _load_policy(root)
    external = policy.get("external_controls", [])
    print(
        "ALIVE: repository-observable enterprise controls verified; "
        f"{len(external)} external controls remain platform-governed"
    )
    for control in external:
        print(f"REFUSED:EXTERNAL_CONTROL {control['id']}: {control['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
