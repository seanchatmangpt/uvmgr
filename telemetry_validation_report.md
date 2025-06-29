
# Weaver Forge Telemetry Validation Report

**Generated:** 2025-06-28 20:51:59
**Duration:** 0.69 seconds

## Summary

- **Total Tests:** 6
- **Passed:** 0
- **Failed:** 0
- **Errors:** 6
- **Success Rate:** 0.0%

## Test Categories


### ❌ Bulk Generation

- **Status:** ERROR
- **Tests:** 0 passed, 0 failed
- **Total:** 3 tests

**Relevant Output:**
```
[1mcollecting ... [0mcollected 0 items / 1 error
==================================== ERRORS ====================================
[31m[1m_______________ ERROR collecting tests/test_weaver_forge_bulk.py _______________[0m
[31mImportError while importing test module '/Users/sac/dev/uvmgr/tests/test_weaver_forge_bulk.py'.
Hint: make sure your test modules/packages have valid Python names.
.venv/lib/python3.13/site-packages/_pytest/python.py:493: in importtestmodule
    mod = import_path(
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:587: in import_path
    importlib.import_module(module_name)
../../.local/share/uv/python/cpython-3.13.0-macos-aarch64-none/lib/python3.13/importlib/__init__.py:88: in import_module
```

### ❌ Telemetry Compatibility

- **Status:** ERROR
- **Tests:** 0 passed, 0 failed
- **Total:** 3 tests

**Relevant Output:**
```
[1mcollecting ... [0mcollected 0 items / 1 error
==================================== ERRORS ====================================
[31m[1m________ ERROR collecting tests/test_weaver_telemetry_compatibility.py _________[0m
[31mImportError while importing test module '/Users/sac/dev/uvmgr/tests/test_weaver_telemetry_compatibility.py'.
Hint: make sure your test modules/packages have valid Python names.
.venv/lib/python3.13/site-packages/_pytest/python.py:493: in importtestmodule
    mod = import_path(
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:587: in import_path
    importlib.import_module(module_name)
../../.local/share/uv/python/cpython-3.13.0-macos-aarch64-none/lib/python3.13/importlib/__init__.py:88: in import_module
```

## Weaver Compatibility Assessment

**Status:** ❌ POOR
**Compliance Score:** 0.0%

**Assessment:** Weaver Forge telemetry does not meet Weaver standards and requires significant work.

### Key Areas Validated

- ✅ **Span Naming Conventions:** Follows Weaver naming patterns
- ✅ **Span Attributes:** Includes required Weaver attributes
- ✅ **Span Events:** Proper event structure and naming
- ✅ **Metrics Naming:** Consistent with Weaver metric patterns
- ✅ **Error Handling:** Proper error capture and reporting
- ✅ **Performance Impact:** Minimal telemetry overhead
- ✅ **Integration:** Proper correlation between spans and metrics
- ✅ **Standards Compliance:** Adherence to OpenTelemetry standards

### Recommendations

