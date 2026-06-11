# Contributing

## Scope

This repository exists to make Codex Desktop project and conversation export/restore safer and easier to verify. Contributions should improve one of these areas:

- packaging correctness
- restore correctness
- compatibility across Codex Desktop updates
- documentation and safety warnings
- reproducible tests

## Development notes

- Keep the scripts dependency-free when possible
- Prefer additive compatibility over schema-specific hacks
- Preserve UTF-8 text output and Windows path handling
- Be conservative around copying user data

## Before opening a PR

1. Run `python -m unittest discover -s tests -p "test_*.py"`.
2. Verify packaging still works against a local test profile.
3. Update `README.md` if flags or behavior change.
4. Call out any behavior that affects privacy, restore semantics, or path mapping.
