---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes. Enforces root cause investigation before any fix attempt.
---

# Systematic Debugging

## Overview

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue: test failures, bugs, unexpected behavior, build failures, integration issues.

**Especially when:**
- Under time pressure
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work

## The Four Phases

Complete each phase before proceeding.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully** - Don't skip. Note line numbers, file paths, error codes.
2. **Reproduce Consistently** - Exact steps? Every time? If not reproducible → gather data, don't guess.
3. **Check Recent Changes** - Git diff, new dependencies, config changes.
4. **Gather Evidence** (multi-component systems) - Log at each boundary. Find WHERE it breaks.
5. **Trace Data Flow** - Where does bad value originate? Fix at source, not symptom.

### Phase 2: Pattern Analysis

- Find working examples in the codebase
- Compare against references (read completely)
- Identify differences between working and broken
- Understand dependencies and assumptions

### Phase 3: Hypothesis and Testing

1. Form single hypothesis: "I think X because Y"
2. Test with SMALLEST possible change
3. One variable at a time
4. Didn't work? Form NEW hypothesis. Don't add more fixes on top.

### Phase 4: Implementation

1. **Create Failing Test** - Before fixing. Use TDD skill.
2. **Implement Single Fix** - ONE change. No "while I'm here."
3. **Verify** - Test passes? No regressions?
4. **If 3+ Fixes Failed** - STOP. Question the architecture. Discuss with user.

## Red Flags - STOP

- "Quick fix for now, investigate later"
- "Just try changing X and see"
- Proposing solutions before tracing data flow
- "One more fix attempt" (when already tried 2+)

## Quick Reference

| Phase | Key Activities |
|-------|----------------|
| 1. Root Cause | Read errors, reproduce, check changes, gather evidence |
| 2. Pattern | Find working examples, compare |
| 3. Hypothesis | Form theory, test minimally |
| 4. Implementation | Create test, fix, verify |

---
*Adapted from [Superpowers](https://github.com/obra/superpowers)*
