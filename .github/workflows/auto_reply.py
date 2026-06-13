import datetime
import json
import os
import textwrap
import urllib.error
import urllib.request

REPO = os.environ["REPO"]
GH_TOKEN = os.environ["GH_TOKEN"]

STATE_FILE = ".github/last_checked.json"
SUMMARY_FILE = os.environ.get("GITHUB_STEP_SUMMARY")
API_ROOT = f"https://api.github.com/repos/{REPO}"


def github_request(path, method="GET", data=None):
    body = None
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "codex-backup-auto-reply",
    }

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        f"{API_ROOT}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        payload = resp.read().decode("utf-8")
        return json.loads(payload) if payload else None


def load_last_checked():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            timestamp = json.load(f).get("timestamp")
            if timestamp:
                return timestamp
    return datetime.datetime.utcnow().isoformat()


def build_reply(author, body):
    if any(kw in body for kw in ["star", "Star", "期待", "不错", "有用", "好用", "支持", "加油"]):
        return textwrap.dedent(
            f"""\
            Thanks for the support @{author}! Glad you find Codex Backup useful.

            If you have any feature requests or run into issues during use, feel free to open a new issue or continue the discussion here. Contributions are always welcome!"""
        ).strip()

    if any(kw in body for kw in ["bug", "error", "问题", "失败", "不行", "issue", "fix", "help"]):
        return textwrap.dedent(
            f"""\
            Thanks for reporting this, @{author}. Could you share more details about your environment (Codex version, Windows version) and the exact steps to reproduce it? A screenshot or error log would be very helpful.

            I’ll look into it and follow up here."""
        ).strip()

    if any(kw in body for kw in ["怎么用", "how", "use", "example", "demo", "文档", "教程", "guide", "install"]):
        return textwrap.dedent(
            f"""\
            Hi @{author}! Please check the README for installation and usage steps:
            https://github.com/{REPO}#readme

            Quick start: install the `.codex-plugin` from the latest release, then in Codex say "backup this project" or "restore from package". If you get stuck on a specific step, reply here and I’ll help."""
        ).strip()

    if any(kw in body for kw in ["pr", "PR", "merge", "提交", "contribute", "fork"]):
        return textwrap.dedent(
            f"""\
            Thanks for your interest in contributing, @{author}! Feel free to open a PR. The project structure is documented in the README.

            If you want to discuss an approach before submitting, just reply here and I’ll help you line it up."""
        ).strip()

    return textwrap.dedent(
        f"""\
        Thanks for the comment, @{author}!

        If you have questions or suggestions about Codex Backup, feel free to share more details. Feature requests are tracked in the open issues, so please mention if there’s already one related to your idea.

        I appreciate you taking the time to engage with the project."""
    ).strip()


last_checked = load_last_checked()
now = datetime.datetime.utcnow().isoformat()
new_comment_rows = []

try:
    issues = github_request("/issues?state=open&per_page=100")
except urllib.error.HTTPError as err:
    print("Failed to list issues:", err.read().decode("utf-8", errors="ignore"))
    raise SystemExit(1)

new_comments_found = False

for issue in issues:
    num = issue["number"]
    try:
        comments = github_request(f"/issues/{num}/comments?per_page=100")
    except urllib.error.HTTPError:
        continue

    for comment in comments:
        created = comment.get("created_at", "") or ""
        author = comment["user"]["login"]
        if created <= last_checked or author == "zdszds2009":
            continue

        new_comments_found = True
        body = comment["body"].strip()
        print(f"\n>>> New external comment on #{num} by @{author}")
        print(f">>> Body: {body[:200]}")
        new_comment_rows.append(
            {
                "issue": num,
                "author": author,
                "created_at": created,
                "body": body,
            }
        )

        reply = build_reply(author, body)
        try:
            github_request(
                f"/issues/{num}/comments",
                method="POST",
                data={"body": reply},
            )
            print("   >> Replied successfully")
        except urllib.error.HTTPError as err:
            error_text = err.read().decode("utf-8", errors="ignore")
            print(f"   >> Reply failed: {error_text[:100]}")

os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump({"timestamp": now}, f)

if not new_comments_found:
    print("\nNo new external comments found.")
else:
    print(f"\nDone. Checked {len(issues)} issues, replied to new comments.")

if SUMMARY_FILE:
    with open(SUMMARY_FILE, "a", encoding="utf-8") as summary:
        summary.write("## Codex Backup auto-reply report\n\n")
        summary.write(f"- Checked at: `{now} UTC`\n")
        summary.write(f"- Open issues scanned: `{len(issues)}`\n")
        if not new_comment_rows:
            summary.write("- New external comments: `0`\n")
        else:
            summary.write(f"- New external comments: `{len(new_comment_rows)}`\n\n")
            for item in new_comment_rows:
                summary.write(f"### Issue #{item['issue']} by @{item['author']}\n\n")
                summary.write(f"- Created at: `{item['created_at']}`\n")
                summary.write("- Comment:\n\n")
                summary.write(
                    f"> {item['body'].replace(chr(10), chr(10) + '> ')}\n\n"
                )
