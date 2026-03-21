---
name: stloop-e2e-hardening
description: End-to-end test hardening checklist for STLoop. Use when modifying tests, CI workflows, Renode/pyOCD integration, builder, or any part of the gen-build-flash-sim pipeline.
---

# STLoop E2E Hardening

## When to Use

Apply this skill when changes touch:
- `tests/` directory (any test file)
- `.github/workflows/` (CI configuration)
- `stloop/builder.py` (build pipeline)
- `stloop/simulators/` (Renode integration)
- `stloop/tester.py` or `stloop/flasher.py` (hardware interaction)
- `tests/e2e_test.py` or `tests/integration/` (E2E entry points)

## Pre-Flight Checklist

Before committing changes, verify each item:

### 1. Local Entry Point
- `python tests/e2e_test.py --skip-simulation` runs without import errors
- The script exercises: prerequisites check, build, Renode script generation

### 2. CI Entry Point Consistency
- `e2e-test.yml` references `tests/e2e_test.py` -- confirm this file exists
- Arguments match: `--skip-simulation` for non-sim jobs, no flag for sim jobs
- Artifact upload path matches where the script writes outputs

### 3. Toolchain Dependencies
Verify these are installed in CI steps before test execution:
- `arm-none-eabi-gcc` (ARM cross-compiler)
- `cmake` >= 3.15
- `ninja` (build system)
- `pip install -e .` (STLoop itself)

### 4. Build Artifact Validation
After a successful build, assert:
- ELF file exists at expected path
- ELF size > 1024 bytes
- ELF contains `main` symbol (use `arm-none-eabi-nm` or Python ELF parser)
- ELF contains `Reset_Handler` symbol

### 5. Renode Script Validation
After script generation, assert:
- `.resc` file exists
- File contains `mach create`
- File contains `sysbus LoadELF`
- File references the correct ELF path

### 6. CI Artifact Upload
- `actions/upload-artifact@v4` step present with `if: always()`
- Retention set (7 days recommended)
- Path covers test report + ELF + .resc

### 7. Failure Diagnostics
On test failure:
- Build stderr/stdout captured and printed
- CMake configuration errors parsed for common patterns
- Suggestion printed (e.g., "run stloop check" or "run stloop cube-download")

## Quick Validation Commands

```bash
# Local smoke test (no hardware, no Renode)
python tests/e2e_test.py --skip-simulation

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests (needs ARM toolchain)
pytest tests/integration/ -v -m integration

# Verify toolchain
arm-none-eabi-gcc --version && cmake --version && ninja --version
```
