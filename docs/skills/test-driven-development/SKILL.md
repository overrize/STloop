---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code. Enforces RED-GREEN-REFACTOR. Use when adding features, fixing bugs, refactoring, or changing behavior.
---

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

## When to Use

**Always:**
- New features
- Bug fixes
- Refactoring
- Behavior changes

**Exceptions (ask the user):**
- Throwaway prototypes
- Generated code
- Configuration files

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over. Delete means delete. Implement fresh from tests.

## Red-Green-Refactor

### RED - Write Failing Test
- One minimal test showing what should happen
- Clear name, one behavior
- Real code (no mocks unless unavoidable)

### Verify RED - Watch It Fail
**MANDATORY.** Run the test. Confirm:
- Test fails (not errors)
- Failure message is expected
- Fails because feature missing (not typos)

Test passes? You're testing existing behavior. Fix test.

### GREEN - Minimal Code
- Simplest code to pass the test
- Don't add features, refactor, or "improve" beyond the test

### Verify GREEN - Watch It Pass
**MANDATORY.** Confirm test passes, other tests pass.

### REFACTOR
After green only: remove duplication, improve names. Keep tests green. Don't add behavior.

## Good Tests

| Quality | Good | Bad |
|---------|------|-----|
| **Minimal** | One thing | `test('validates email and domain and whitespace')` |
| **Clear** | Name describes behavior | `test('test1')` |
| **Shows intent** | Demonstrates desired API | Obscures what code should do |

## Red Flags - STOP and Start Over

- Code before test
- Test passes immediately
- Can't explain why test failed
- "I'll write tests after"
- "Keep as reference" or "adapt existing code"

## Bug Fix Workflow

1. Write failing test reproducing the bug
2. Verify it fails
3. Write minimal fix
4. Verify it passes

Never fix bugs without a test.

## Verification Checklist

- [ ] Every new function has a test
- [ ] Watched each test fail before implementing
- [ ] Wrote minimal code to pass
- [ ] All tests pass
- [ ] Edge cases covered

---
*Adapted from [Superpowers](https://github.com/obra/superpowers)*
