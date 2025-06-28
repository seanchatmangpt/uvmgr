# Dependency Management

uvmgr wraps `uv` to provide a simple interface for managing dependencies.

## Add a Dependency

```bash
uvmgr deps add "requests"
```

## Remove a Dependency

```bash
uvmgr deps remove "requests"
```

## List Dependencies

```bash
uvmgr deps list
```

All changes are reflected in your `pyproject.toml` and lock file automatically. 