# Chinese Outreach Kit

Use this file when asking friends or other GitHub users to review Codex Backup. The goal is honest public feedback from their own GitHub accounts. Do not post on someone else's behalf.

## Short SMS / WeChat message

我最近做了一个开源小工具 Codex Backup，主要用于把本机 Codex Desktop 的项目对话、thread 记录和必要的恢复信息打包成可迁移的备份包，适合换电脑、重装环境或保留调试上下文时使用。

项目地址：
https://github.com/zdszds2009/codex-backup

如果你方便的话，想请你帮我做一个很小的公开测试：打开仓库看一下 README，如果你用 Windows + Codex Desktop，也可以运行 `--list` 或只按文档检查流程。然后在 GitHub 上 star 一下，并在 issue 里留一条真实反馈，例如“文档是否看得懂、这个工具是否对你的 Codex 使用场景有帮助、哪里需要改进”。不用夸，真实反馈最有价值。

## More detailed message

我在准备 OpenAI 的 Codex for Open Source 申请，所以需要一些真实的外部使用和反馈信号。这个项目不是通用备份软件，而是专门解决 Codex Desktop 本地项目/对话恢复的问题：避免手动复制 `.codex` 文件或直接改 SQLite。

你可以帮忙做其中任意一项：

1. 打开仓库，阅读 README，并 star 项目。
2. 如果你有 Windows 和 Codex Desktop，运行 `python .\scripts\build_restore_package.py --list`，看看是否能列出本机项目和对话。
3. 在 GitHub issue 里留下真实反馈，说明你是否理解这个工具、是否会用到、希望补什么安全检查或功能。
4. 如果发现问题，请直接开 bug issue。

项目地址：
https://github.com/zdszds2009/codex-backup

## Friend testing steps

### Lowest-risk review

1. Open `https://github.com/zdszds2009/codex-backup`.
2. Read the first half of `README.md`.
3. Check whether the purpose is clear.
4. Star the repository if you think it is useful.
5. Open a GitHub issue using the usage feedback template.

### Windows + Codex Desktop smoke test

1. Clone the repository or download the source zip.
2. Open PowerShell in the project folder.
3. Run:

```powershell
python .\scripts\build_restore_package.py --list
```

4. Do not share private thread IDs or sensitive project paths publicly.
5. Open a GitHub issue with a short sanitized result.

### Package inspection test

Only do this if the tester is comfortable creating a local test package.

1. Create a package from a safe test thread or test project.
2. Run:

```powershell
python .\scripts\inspect_package.py "C:\path\to\package.zip"
```

3. Confirm whether the summary is understandable before restore.
4. Leave feedback on whether the package review output is clear enough.

## GitHub issue reply templates

### Template A: README-only review

Title:

```text
[feedback] README review from a Codex Desktop user
```

Body:

```text
I reviewed the README and the project goal is clear to me: this tool packages selected Codex Desktop conversations and optional project files for migration or recovery.

My environment:
- Windows: yes/no
- Codex Desktop user: yes/no

What was clear:
- The difference between thread-only export and project-file export is understandable.
- The safety warning about inspecting packages before sharing is useful.

What could be improved:
- <write one concrete suggestion, or say "No major suggestion from README-only review.">

Would this help my workflow?
- <yes/no/maybe, with one sentence explaining why>
```

### Template B: `--list` smoke test

Title:

```text
[feedback] build_restore_package --list smoke test
```

Body:

```text
I ran the low-risk list command from the README.

Environment:
- Windows version: <example: Windows 11>
- Python version: <example: 3.11>
- Codex Desktop installed: yes/no

Command:
python .\scripts\build_restore_package.py --list

Result:
- The command completed: yes/no
- It found expected projects/conversations: yes/no/partially
- I am not posting private project paths or thread IDs publicly.

Feedback:
- <one or two sentences about whether the output was understandable>
```

## Important integrity note

