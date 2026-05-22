# gomtm-agent-workflow Implementation Plan

> **For Hermes:** Implement this plan directly in the current session. This is documentation-only skill work; keep changes surgical and concise.

**Goal:** 完善并全局安装 `gomtm-agent-workflow` 技能，使其成为 gomtm/mtm 的 Issue + Kanban + 多 Agent + Telegram 审批工作流入口。

**Architecture:** 保留现有 skill 目录。主 `SKILL.md` 做短入口；长一点的审批、Kanban graph、bridge、模板内容放入单个 reference。只引用 `gomtm-hermes` 等已有技能，不重复 Hermes 安装/配置细节。

**Tech Stack:** Markdown SKILL.md、Agent Skills frontmatter、`npx skills` discovery、`gomtm skills link` symlink 安装。

---

### Task 1: Rewrite the skill entry document

**Objective:** 将 `SKILL.md` 收敛为精简入口，保持触发条件清晰、规则可执行。

**Files:**

- Modify: `skills/mtmskills/gomtm-agent-workflow/SKILL.md`

**Steps:**

1. 保留 frontmatter：`name: gomtm-agent-workflow`，description 写触发条件，不写详细流程摘要。
2. 正文保留以下短章节：
   - Overview
   - When to Use
   - Source of Truth Split
   - Default Flow
   - Required Sub-skills
   - Approval Gate Rules
   - Repository Routing
   - Acceptance Evidence
   - Common Pitfalls
   - Verification Checklist
3. 删除或压缩会重复 `gomtm-hermes` 的 Hermes 具体配置说明。
4. 在正文末尾引用：`references/github-issue-kanban-approval.md`。

**Verification:**

Run a small Python frontmatter check after writing:

```bash
python - <<'PY'
from pathlib import Path
import yaml
p = Path('skills/mtmskills/gomtm-agent-workflow/SKILL.md')
s = p.read_text()
assert s.startswith('---\n')
fm_text, body = s[4:].split('\n---\n', 1)
fm = yaml.safe_load(fm_text)
assert fm['name'] == 'gomtm-agent-workflow'
assert fm['description'].startswith('Use when')
assert len(fm['description']) <= 1024
assert body.strip()
print('OK')
PY
```

Expected: `OK`.

### Task 2: Add the workflow reference

**Objective:** 添加一份短 reference，承载执行前评论、approval sync、Kanban graph、bridge、最终汇总模板。

**Files:**

- Create: `skills/mtmskills/gomtm-agent-workflow/references/github-issue-kanban-approval.md`

**Steps:**

1. 创建 `references/` 目录。
2. 写入以下章节：
   - Pre-execution Issue Comment
   - Approval Sync
   - Minimal Kanban Graph
   - Bridge Choices
   - Idempotency
   - Final Issue Summary
3. 命令示例使用 `<repo>`, `<issue-number>`, `<task-id>`, `<profile>` 占位符。
4. 不写真实 token、域名、一次性路径。

**Verification:**

```bash
test -s skills/mtmskills/gomtm-agent-workflow/references/github-issue-kanban-approval.md
python - <<'PY'
from pathlib import Path
s = Path('skills/mtmskills/gomtm-agent-workflow/references/github-issue-kanban-approval.md').read_text()
for needle in ['Pre-execution Issue Comment', 'Approval Sync', 'Minimal Kanban Graph', 'Final Issue Summary']:
    assert needle in s
print('OK')
PY
```

Expected: `OK`.

### Task 3: Verify discovery and install globally

**Objective:** 确认 mtmskills 能发现该技能，并通过源码 symlink 方式全局安装。

**Files:**

- No source edits expected.

**Steps:**

1. Run discovery:

```bash
npx -y skills add . --list
```

2. Confirm output includes `gomtm-agent-workflow`.
3. Preview install:

```bash
gomtm skills link . --dry-run
```

4. Apply install:

```bash
gomtm skills link .
```

5. Confirm linked global path exists, using `readlink` or `test -e` for the expected user-level skill location if output shows it.

**Expected:** discovery includes `gomtm-agent-workflow`; install command exits 0.

### Task 4: Commit the skill changes

**Objective:** 提交 skill 与 reference，保持 spec commit 与 implementation commit 分离。

**Files:**

- `skills/mtmskills/gomtm-agent-workflow/SKILL.md`
- `skills/mtmskills/gomtm-agent-workflow/references/github-issue-kanban-approval.md`

**Steps:**

```bash
git diff --check
git status --short
git add skills/mtmskills/gomtm-agent-workflow
git commit -m "Add gomtm agent workflow skill"
```

**Expected:** commit succeeds.

### Task 5: Final verification report

**Objective:** 回报完成状态前提供证据。

**Steps:**

1. Re-run `git status --short`.
2. Report:
   - files changed;
   - discovery command result;
   - install command result;
   - commit hash.

**Expected:** no uncommitted changes except unrelated pre-existing files, if any. If unrelated blockers appear, report precisely.
