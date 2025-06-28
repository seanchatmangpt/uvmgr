# GitHub Actions API Command Group

The `uvmgr actions` command group provides a comprehensive, enterprise-grade interface to GitHub Actions, with full OpenTelemetry instrumentation and Weaver semantic conventions. This suite enables you to monitor, manage, and automate your CI/CD workflows directly from the command line.

## Overview

- **Telemetry**: All commands are fully instrumented with OpenTelemetry and Weaver conventions for observability.
- **Token Management**: Uses your GitHub CLI token by default, or accepts a `--token` argument.
- **Modern UX**: Beautiful, readable output and robust error handling.

## Subcommands

### `status`
Show recent workflow runs for a repository.

```sh
uvmgr actions status --owner <org> --repo <repo> [--limit N] [--token <token>]
```

**Options:**
- `--owner` (required): GitHub owner/org name
- `--repo` (required): GitHub repository name
- `--limit`: Number of runs to show (default: 10)
- `--token`: GitHub token (optional)

---

### `workflows`
List all workflows in a repository.

```sh
uvmgr actions workflows --owner <org> --repo <repo> [--token <token>]
```

---

### `run`
Get detailed information about a specific workflow run.

```sh
uvmgr actions run --owner <org> --repo <repo> --run-id <id> [--token <token>]
```

---

### `jobs`
List jobs for a specific workflow run.

```sh
uvmgr actions jobs --owner <org> --repo <repo> --run-id <id> [--token <token>]
```

---

### `logs`
Get logs for a workflow run or a specific job.

```sh
uvmgr actions logs --owner <org> --repo <repo> --run-id <id> [--job-id <job_id>] [--token <token>]
```

---

### `cancel`
Cancel a running workflow.

```sh
uvmgr actions cancel --owner <org> --repo <repo> --run-id <id> [--token <token>]
```

---

### `rerun`
Rerun a workflow (optionally only failed jobs).

```sh
uvmgr actions rerun --owner <org> --repo <repo> --run-id <id> [--failed-only] [--token <token>]
```

---

### `artifacts`
List artifacts for a workflow run.

```sh
uvmgr actions artifacts --owner <org> --repo <repo> --run-id <id> [--token <token>]
```

---

### `secrets`
List repository secrets (names only).

```sh
uvmgr actions secrets --owner <org> --repo <repo> [--token <token>]
```

---

### `variables`
List repository variables.

```sh
uvmgr actions variables --owner <org> --repo <repo> [--token <token>]
```

---

### `usage`
Show GitHub Actions usage for a repository.

```sh
uvmgr actions usage --owner <org> --repo <repo> [--token <token>]
```

---

## Example Workflow

```sh
# List all workflows
uvmgr actions workflows --owner seanchatmangpt --repo uvmgr

# Show recent workflow runs
uvmgr actions status --owner seanchatmangpt --repo uvmgr --limit 5

# Get details for a specific run
uvmgr actions run --owner seanchatmangpt --repo uvmgr --run-id 123456789

# List jobs for a run
uvmgr actions jobs --owner seanchatmangpt --repo uvmgr --run-id 123456789

# Get logs for a run
uvmgr actions logs --owner seanchatmangpt --repo uvmgr --run-id 123456789

# Cancel a workflow run
uvmgr actions cancel --owner seanchatmangpt --repo uvmgr --run-id 123456789

# Rerun a workflow
uvmgr actions rerun --owner seanchatmangpt --repo uvmgr --run-id 123456789

# List artifacts
uvmgr actions artifacts --owner seanchatmangpt --repo uvmgr --run-id 123456789

# List secrets
uvmgr actions secrets --owner seanchatmangpt --repo uvmgr

# List variables
uvmgr actions variables --owner seanchatmangpt --repo uvmgr

# Show usage
uvmgr actions usage --owner seanchatmangpt --repo uvmgr
```

## Telemetry & Observability

All commands emit OpenTelemetry spans and metrics, using Weaver semantic conventions for:
- Command arguments and options
- API endpoints and HTTP status
- Result counts and error metrics

## See Also
- [OpenTelemetry Integration](opentelemetry-integration.md)
- [Weaver Integration](weaver-integration.md) 