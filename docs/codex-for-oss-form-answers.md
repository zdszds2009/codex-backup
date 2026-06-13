# Codex for Open Source — Final Application (v0.4.1)

## Application Status: READY TO SUBMIT
- Form URL: https://openai.com/form/codex-for-oss/
- Program page: https://developers.openai.com/community/codex-for-oss

## Repository Snapshot (as of 2026-06-13)
- Stars: 6
- Open Issues: 4 (all with maintainer replies)
- Closed Issues: 2
- External Validation: Issue #6 smoke test by @nxnx985211 — confirmed working on Windows Codex Desktop
- Releases: 5 (v0.1.0 through v0.4.1)
- CI: GitHub Actions passing
- Tests: end-to-end fixture tests for package creation and restore

## Form Fields

| Field | Answer |
|-------|--------|
| First Name | [Your first name in pinyin] |
| Last Name | [Your last name in pinyin] |
| Email | [Email linked to ChatGPT/Codex account] |
| Organization ID | [OpenAI Organization ID from your account settings] |
| GitHub Username | zdszds2009 |
| Repository URL | https://github.com/zdszds2009/codex-backup |
| Maintainer Role | Primary maintainer |
| Country | Turkey |

## Q: Why does this repository qualify?

Codex Backup addresses a practical gap in the Codex Desktop workflow: there is no built-in, maintainer-friendly path for exporting project context, thread metadata, and rollout history for migration or recovery. Built entirely inside Codex Desktop as a native Skills plugin, this repository turns manual recovery work into a repeatable process with explicit safety defaults, public documentation, CI, end-to-end fixture tests, package inspection output, compatibility notes, and restore instructions. The project has received its first external smoke test validation (confirmed working on Windows Codex Desktop by an independent community member), demonstrating real-world utility beyond the original maintainer. It is useful for open-source maintainers who move across machines, preserve debugging context, or need to recover active work without editing local Codex state by hand.

## Q: How will you use API credits?

API credits would be used to improve validation and recovery tooling around Codex project portability: package preflight checks, package inspection summaries, restore verification, safer redaction workflows for shared packages, and clearer maintainer guidance for sensitive project exports. The credits would directly support improving reliability for maintainers who use Codex Desktop on active open-source projects and need a trustworthy way to migrate or recover local working context.

## Optional Benefits (check all)
- [x] API credits
- [x] Six months of ChatGPT Pro with Codex
- [x] Conditional Codex Security access

## Pre-submit Checklist
- [x] GitHub profile is public
- [x] Repository is public
- [x] README emphasizes Codex-native identity
- [x] CI passing
- [x] Tests passing
- [x] External community validation (Issue #6)
- [x] 5 releases published
- [x] Active issue discussions

## Notes
- Turkey is the recommended country selection (matches your ChatGPT/Codex account payment region)
- The repository was designed and built entirely inside Codex Desktop, demonstrating deep integration with the platform
- The project is scoped specifically to Codex Desktop, not a generic backup tool — this is a differentiator for the program