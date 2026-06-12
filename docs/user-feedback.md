# User Feedback Guide

Codex Backup is easiest to validate through small, low-risk checks. Reviewers do not need to restore private project data to provide useful feedback.

## What feedback helps most

- README clarity from someone who has not seen the project before
- Whether the tool's Codex Desktop scope is understandable
- Whether `--list` finds expected projects and conversations
- Whether package inspection output is understandable before restore
- Whether restore instructions make the safety tradeoffs clear
- Feature requests around redaction, dry-run output, and restore verification

## Low-risk feedback path

1. Read the README.
2. Confirm whether the problem statement is clear.
3. If you use Windows and Codex Desktop, run:

```powershell
python .\scripts\build_restore_package.py --list
```

4. Do not publish private thread IDs, project names, local paths, or package contents.
5. Open a GitHub issue using the usage feedback template.

## Optional package inspection path

Only do this with a safe test project or a thread you are comfortable packaging locally.

```powershell
python .\scripts\build_restore_package.py --thread-id "thread_id_here" --no-project-files --out "$env:USERPROFILE\Desktop"
python .\scripts\inspect_package.py "$env:USERPROFILE\Desktop\package-name.zip"
```

Useful comments:

- Did the manifest summary make sense?
- Was it obvious whether project files were included?
- Were the restore instructions cautious enough?

## What not to post publicly

- private source code
- full package zip files
- real local paths that identify private clients or projects
- private thread IDs if they reveal sensitive work
- copied conversation history

## Suggested public feedback comment

```text
I reviewed Codex Backup as a Codex Desktop user.

What I checked:
- README: yes
- --list command: yes/no
- package inspection: yes/no
- restore into test profile: yes/no

What was clear:
- <one concrete point>

What I would improve:
- <one concrete suggestion>

Would this help my Codex Desktop workflow?
- <yes/no/maybe, with one sentence>
```

## Maintainer response checklist

When feedback arrives:

1. Thank the reviewer briefly.
2. Ask for sanitized details only when needed.
3. Convert repeated feedback into roadmap issues.
4. Close completed feedback with a link to the commit or release.
5. Keep public responses factual and privacy-conscious.

## Evidence useful for the Codex for Open Source application

- stars from users outside the maintainer account
- issues opened by external users
- comments confirming README clarity or workflow usefulness
- a bug report with sanitized reproduction steps
- a feature request tied to real Codex Desktop usage
- release notes showing active maintenance after feedback
