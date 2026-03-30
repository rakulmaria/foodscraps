# Foodscraps

> TODO: Introduction text here.

## Commit Message Guidelines

Commits that don't follow the [Conventional Commits](https://www.conventionalcommits.org/) hooks will be rejected. Here follows a guide on how to commit properly.

### Format
```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

- **`type`** — required, lowercase
- **`scope`** — optional, lowercase, describes what part of the codebase is affected
- **`subject`** — required, lowercase, no trailing period, max 100 characters total in the header

---

### Acceptable types

| Type | When to use |
|----------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting, whitespace — no logic changes |
| `refactor` | Code restructuring without fixing a bug or adding a feature |
| `perf` | Performance improvements |
| `test` | Adding or updating tests |
| `build` | Changes to the build system or external dependencies |
| `ci` | Changes to CI configuration or scripts |
| `chore` | Miscellaneous tasks that don't change source or tests |
| `revert` | Reverting a previous commit |

---

### Examples
```bash
# Minimal
git commit -m "fix: handle null response from API"

# With scope
git commit -m "feat(auth): add OAuth2 login flow"

# With body
git commit -m "refactor(db): simplify query builder

Extracted filter logic into a separate helper function
to improve readability and testability."

# Breaking change via footer
git commit -m "feat(api)!: drop support for v1 endpoints

BREAKING CHANGE: all v1 routes have been removed, migrate to v2."
```

---

### Breaking Changes

A breaking change can be signalled in two ways:
```bash
# Using ! after the type
feat!: remove deprecated config option

# Using a footer
feat: remove deprecated config option

BREAKING CHANGE: the `legacyMode` config key is no longer supported.
```
