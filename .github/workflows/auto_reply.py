import os, json, subprocess, datetime, re, textwrap

REPO = os.environ["REPO"]
GH_TOKEN = os.environ["GH_TOKEN"]

STATE_FILE = ".github/last_checked.json"
SUMMARY_FILE = os.environ.get("GITHUB_STEP_SUMMARY")

def run_gh(*args):
    return subprocess.run(
        ["gh", f"--repo={REPO}"] + list(args),
        capture_output=True, text=True,
        env={**os.environ, "GH_TOKEN": GH_TOKEN}
    )

# Load last check time
last_checked = None
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        last_checked = json.load(f).get("timestamp")
if not last_checked:
    last_checked = datetime.datetime.utcnow().isoformat()

now = datetime.datetime.utcnow().isoformat()
new_comment_rows = []

# Fetch all open issues
result = run_gh("issue", "list", "--state=open", "--json=number,title,comments,updatedAt")
if result.returncode != 0:
    print("Failed to list issues:", result.stderr)
    exit(1)

issues = json.loads(result.stdout)

new_comments_found = False

for issue in issues:
    num = issue["number"]
    # Fetch comments for this issue
    res = run_gh("api", f"/repos/{REPO}/issues/{num}/comments")
    if res.returncode != 0:
        continue
    comments = json.loads(res.stdout)
    for comment in comments:
        created = comment.get("created_at", "") or ""
        if created > last_checked and comment["user"]["login"] != "zdszds2009":
            new_comments_found = True
            body = comment["body"].strip()
            author = comment["user"]["login"]
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

            # Determine reply based on comment content
            if any(kw in body for kw in ["star", "Star", "期待", "不错", "有用", "好用", "支持", "加油"]):
                reply = textwrap.dedent(f"""\
                    Thanks for the support @{author}! Glad you find Codex Backup useful.
                    
                    If you have any feature requests or encounter any issues during use, feel free to open a new issue or comment here. Contributions are always welcome!""")
            elif any(kw in body for kw in ["bug", "error", "问题", "失败", "不行", "bug", "issue", "fix", "help", "help"]):
                reply = textwrap.dedent(f"""\
                    Thanks for reporting @{author}. Could you share more details about your environment (Codex version, Windows version) and the exact steps to reproduce? A screenshot or error log would be very helpful.
                    
                    I'll look into this and get back to you.""")
            elif any(kw in body for kw in ["怎么用", "how", "use", "example", "demo", "文档", "教程", "guide", "install"]):
                reply = textwrap.dedent(f"""\
                    Hi @{author}! Check the README for installation and usage steps:
                    https://github.com/{REPO}#readme
                    
                    Quick start: install the `.codex-plugin` from the latest release, then in Codex say \"backup this project\" or \"restore from package\". Let me know if you need help with a specific step!""")
            elif any(kw in body for kw in ["pr", "PR", "merge", "提交", "contribute", "fork"]):
                reply = textwrap.dedent(f"""\
                    Thanks for your interest in contributing @{author}! Feel free to submit a PR. The project structure is documented in the README.
                    
                    If you have questions about the codebase or want to discuss your approach before opening a PR, just ask here. Happy to help!""")
            else:
                reply = textwrap.dedent(f"""\
                    Thanks for the comment @{author}!
                    
                    If you have questions or suggestions about Codex Backup, feel free to share more details. Feature requests are tracked in the open issues — check if there's already one matching your idea.
                    
                    Appreciate you taking the time to engage with the project!""")
            
            reply = reply.strip()
            res2 = run_gh("api", f"/repos/{REPO}/issues/{num}/comments", "-f", f"body={reply}")
            if res2.returncode == 0:
                print(f"   >> Replied successfully")
            else:
                print(f"   >> Reply failed: {res2.stderr[:100]}")

# Save state
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
with open(STATE_FILE, "w") as f:
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
