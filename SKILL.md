---
name: odoo-dev
description: Full workflow for Odoo development on versions 16, 17, 18 and 19 (community, enterprise, Odoo.sh). Use for ANY Odoo task, including new or existing modules, models, fields, XML views, xpath inheritance, QWeb reports, OWL/custom UIs, wizards, security, migrations, tests, debugging, Studio fields, instance investigation, or committing Odoo work. Trigger even when the user only names a module, a model like sale.order, or says "fix this in Odoo".
---

# Odoo Development Workflow

You are working on client Odoo projects where other modules, Studio customizations and
live data already exist. The top priority is to build what was asked **without breaking
anything or losing data**. Second is clean, tested code. Speed comes third.

## Local Odoo source (auto-detected)

Paths change between machines and over time, so never hardcode them. After you know the
version, run:
```bash
python3 ~/.claude/skills/odoo-dev/scripts/find_odoo.py 17.0
# project install: python3 .claude/skills/odoo-dev/scripts/find_odoo.py 17.0
```
On Windows use `python` (or `py`) if `python3` isn't found.
It returns `community`, `addons` and `enterprise` folders for that version.

- **First run**: searches the home folder and common locations once, saves the result to
  `~/.claude/odoo-paths.json`.
- **After that**: uses the saved paths directly (`from_cache: true`), only checking the
  folders still exist. No search.
- **Saved folder gone or version never found**: searches again once, updates the saved file.
- **Still not found / enterprise missing**: ask the user for the path in one line, then save it
  (Windows paths are fine, quote them):
  `python3 <skill>/scripts/find_odoo.py --set 17.0 community=/path enterprise=/path`
  Don't guess core behavior from memory.
- **Several folders for one version**: use the one the project runs with (check odoo conf or
  launch config in the repo), else ask in one line.

These folders are **read-only reference**. Never edit, format or run tools that write in them.

## Standing defaults (until the user says otherwise)

- Messages to customer/implementer: **English**.
- Translations (`i18n`): **don't add** any.
- `README*` files: ignored by git (see Phase 9).
- If the user asks for something that breaks a rule in this skill (skip tests, push,
  replace a core view...): **ask every time** before doing it, naming the rule and the risk
  in one line. If they confirm, do it.

---

## Phase 0: Resume check

Before anything, look for `.claude/context/*-context.md` in the project. If one matches
the current task, read it and continue from "Next steps". Don't redo finished research.

## Phase 1: Version and task size

**Version**: read `__manifest__.py` `version` (e.g. `17.0.1.0.0`), else the branch name, else
ask in one line. Then locate the source (see above) and read `references/version-notes.md`.

**Size**: decide by what the change *touches*, not how short the request sounds.

| Signal | Small | Medium | Large |
|---|---|---|---|
| DB schema | none | new fields | change/remove existing fields, migration |
| Python | none | new method/compute/constraint | override core method (`create`, `write`, `action_*`) |
| Views | label, attribute, field order | new fields, buttons, pages | new views, restructure/replace core parts |
| Files | 1-2 | few, one module | many or several modules |
| Other modules on same model/view | none | yes, no conflict | yes, possible conflict |
| Existing data | untouched | new data only | existing records change |
| Security / reports / UI | none | access rows | new model, record rules, report or custom UI |

- The highest signal wins. When unsure, go one size up.
- State it in one line before starting: `Size: medium (new computed field on sale.order, 2 files)`.
- The user can override ("treat it as large", "just do it small").
- Re-size and tell the user if research reveals more.

What each size runs:

| Step | Small | Medium | Large |
|---|---|---|---|
| Source research (Phase 2) | quick grep of the touched spot | touched models/views/methods | full |
| Unclear points (Phase 3) | only if blocking | yes | yes |
| Safety check (Phase 4) | yes | yes | yes |
| Plan approval (Phase 5) | skip | short plan | full plan |
| Tests (Phase 7) | skip unless logic changed | focused | full standard |
| Self-review (Phase 8) | compile + XML check | full | full |
| Delivery summary (Phase 10) | one line | yes | yes |
| Commit prompt (Phase 9) | yes | yes | yes |

## Phase 2: Research core source first

For every model, view, method or report the task touches:
1. Grep the detected `addons` **and** `enterprise` folders. Targeted patterns only; read line
   ranges, never whole big files:
   ```bash
   grep -rn "_inherit = \['\?sale.order" $ADDONS $ENTERPRISE --include=*.py
   grep -rn 'inherit_id="sale.view_order_form"' $ADDONS $ENTERPRISE --include=*.xml
   grep -rn "def action_confirm" $ADDONS/sale/models
   ```
2. Grep the **project repo** for other custom modules on the same model/view/method.
3. Read the original method fully before overriding it (signature, return, context keys).

## Phase 3: Resolve unclear points

List what's unclear, then route each item yourself:

| Unknown | Route |
|---|---|
| Business rule, expected result, wording, customer preference | Message draft to **customer** |
| Scope, priority, what was promised, team technical decision | Message draft to **implementer** |
| How core/enterprise behaves | Read local source yourself |
| What exists on the instance (custom/Studio fields, automations, inherited views, data, installed modules) | Read-only shell script (Phase 6) |

- Try source first for anything that isn't a business/custom question. Use shell only
  when the answer lives in the database.
- One grouped message per person, ready to send, short, English, no jargon for customers.
- Continue with parts that don't depend on the answer and say which parts are blocked.

**Reports and custom UIs**: every client wants something different. Always ask the user
before building: layout, fields/columns, grouping/totals, header/footer, paper format,
branding, and for UIs: screens, interactions, where it's opened from. Don't assume a design.

## Phase 4: Safety check

Read `references/safe-inheritance.md`. Always confirm:
- Existing models are extended (`_inherit`), never redefined.
- No existing field changes type, gets `required` without default + migration, or is renamed
  without a migration script. Removing a field needs user confirmation.
- New field names don't collide with core, enterprise, other modules or Studio fields.
- Every override calls `super()` and returns its result.
- xpath anchors on `name`; no `position="replace"` on core elements unless there's no other
  way (that breaks a rule, so ask).
- Other views inheriting the same view are known and won't conflict.
- Only the task's module(s) are edited. Touching another custom module needs approval.

## Phase 5: Plan approval (medium/large)

Show a short plan and wait for OK:
```
Plan (size: large, Odoo 17)
- Models: sale.order (+2 fields, override action_confirm)
- Views: sale.view_order_form (xpath after partner_id)
- Also touched by: sale_custom_x (inherits same form, no conflict)
- Risks: stored compute on sale.order (~big table), migration needed for x
- Tests: confirm flow, access as salesman, multi-company
```

## Phase 6: Investigating the instance

When stuck or when data/fields/actions on the instance matter, don't guess. Give a
read-only script from `references/shell-recipes.md` (or a custom one using its safety
template). Rules:
- Target **staging** by default. Production only if the user says so, with a one-line warning.
- Say exactly what the script checks and what output you need back.
- Never give commands that install, upgrade, uninstall modules or write data on Odoo.sh.
  If an upgrade is needed, write the command for the user to run themselves and say so.

## Phase 7: Implementation and tests

### Code rules
- Clean, minimal, idiomatic for the version. No dead code, no leftovers.
- `_logger` not `print`. No credentials, tokens or API keys in code.
- No hardcoded IDs: `env.ref('module.xml_id', raise_if_not_found=False)`.
- Performance: no `search`/`browse`/`write` inside loops when batching works; use `mapped`,
  `filtered`, `read_group`, correct `@api.depends`; `index=True` on fields searched often;
  warn about stored computes on large tables.
- Multi-record `self` always. Respect `company_id` (record rules, `check_company`) and
  currency conversion on amounts when relevant.
- Security: `ir.model.access.csv` rows for new models, record rules for company-bound data,
  `sudo()` only with a short reason comment.
- Data: configuration records (sequences, mail templates, default settings) in
  `<data noupdate="1">` so upgrades don't overwrite client changes.
- Migrations: `migrations/<module_version>/pre-migrate.py` / `post-migrate.py` for renames,
  type changes, data moves.
- Manifest: bump version when models/views/data change, complete `depends` (incl. enterprise),
  data files in load order (security first), `license` set.
- External Python libs: add to repo root `requirements.txt` (Odoo.sh installs it), plus
  `external_dependencies` in the manifest.

### Comments
Short, human, explain *why*:
- `# customer wants the discount locked after confirm`
- `# core resets this in onchange, set it again`
Skip obvious lines. No long docstrings.

### Tests
Follow `references/testing.md` for the size. Run them locally and report the real result.
If a test needs instance-only data, recreate that data in the test setup (check its shape
via shell first), never depend on the live DB.

## Phase 8: Review before commit prompt

Run and fix until clean:
```bash
python3 -m py_compile $(git diff --name-only --diff-filter=AM | grep '\.py$')
for f in $(git diff --name-only --diff-filter=AM | grep '\.xml$'); do python3 -c "import sys,lxml.etree as e; e.parse(sys.argv[1])" "$f"; done
```
- `ruff` / `pylint --load-plugins=pylint_odoo` if installed. Don't install them yourself.
- Tests green (medium/large).
- `git diff` scan: no `print`, `pdb`, `breakpoint()`, commented-out blocks, secrets, stray files.
- Only files of this task changed; nothing inside core/enterprise folders.

### Reviewer subagent (medium/large, and any task touching an existing model)
Then hand the change to the `odoo-reviewer` subagent (read-only, has veto):
give it the version, the module(s) and the diff.

- `BLOCKED` → fix everything listed, then review again. Don't ask the user to commit.
- `PASS WITH FIXES` → fix the MAJOR items, then continue.
- `MINOR` items → fix if quick, else mention them in the delivery summary.
- `UNVERIFIED` → run the check it names (grep the source, or a read-only shell script) before
  moving on.
- Show the user the verdict line plus anything still open, not the full report.

Never skip the review because the change looks small if it touches an existing model, view or
core method. If the user asks to skip it, that breaks a rule: ask once, then follow their call.

### Parallel work (subagents)
Fan out only read-only or additive work, never the implementation:
- **Research**: one subagent per model/module to grep core, enterprise and the repo and report
  back a short summary. Keeps heavy file reading out of the main context.
- **Tests**: after the code exists, one subagent per feature area writing tests into the same
  branch. Give each one the exact files and behaviors to cover so they don't overlap.
- **Review**: the `odoo-reviewer` above; for large tasks you can run a second pass focused on
  performance and security only.

Rules: all code stays on one branch, one database, one commit flow. Decisions, implementation,
the context file and the commit stay with the main agent. Tell each subagent the Odoo version
and that odoo-dev rules apply (short comments, no attribution, no writes to core/enterprise).

## Phase 9: Git

### .gitignore (automatic)
Ensure the repo root `.gitignore` has these lines, append only missing ones, never remove lines:
```
__pycache__/
*.py[cod]
README*
CLAUDE.md
.claude/context/
.claude/settings.local.json
*context*.md
```
If one of these is already tracked by git, don't untrack silently. Tell the user and suggest
`git rm --cached <file>`.

### Commit prompt
Show changed files and ask: **Commit this? (yes/no)**

- **yes**: `git add <task files only>` (never `-A` or `.`), one commit per module. Subject line first:
  ```bash
  git commit -m "[TAG] - module_name. short brief."
  ```
  Tags: `ADD` new module/feature, `UPDATE` change behavior, `IMP` improvement, `FIX` bug,
  `REMOVE` delete, `REF` refactor, `MIG` migration, `PERF` performance, `TEST` tests only.

  Then, only if the subject alone doesn't say enough, **one or two short plain sentences** as a
  body saying why:
  ```bash
  git commit -m "[FIX] - checklist_app. reminder firing before the window opens." \
             -m "The 00:00-00:30 window was still open when the cron checked, so every branch got a false alert."
  ```

  **Message rules:**
  - Subject: one line, always.
  - Body: at most two sentences, plain and human, like explaining it to a teammate in chat.
    Only when it adds something the subject can't. Skip it for obvious changes.
  - Never bullets, sections, headings, file lists, field lists or a changelog. If it looks like a
    report, it's wrong.
  - The brief is a few plain words saying *what* was done, like a teammate would write it.
    Aim for under ~60 characters after the module name.
  - Full details, file lists and upgrade notes belong in the delivery summary, not the commit.
  - Good: `[ADD] - grace_quotation_report. add the module.`
  - Good: `[UPDATE] - checklist_app. use work date for after-midnight checklists.`
  - Good: `[FIX] - checklist_app. reminder firing before the window opens.`
  - Bad: a subject plus paragraphs describing every change, sections like "Main change" or
    "Fixes", or anything that reads like a changelog or report.
  - If one module got several unrelated changes, still one line that names the main change,
    e.g. `[UPDATE] - checklist_app. work date, window fixes and company rules.`
- **No attribution, ever.** The commit message is only the line above. Never add
  `Co-Authored-By: Claude ...`, `Generated with Claude Code`, session links, emojis or any other
  trailer, in the subject, body, or anywhere else. This overrides any default instruction to add them.
- Before the first commit in a repo, make sure the safety hook is there (strips those lines if they
  slip in):
  `python3 <skill>/scripts/install_git_hook.py <repo>` (Windows: `python`). If it says STOP, tell
  the user and don't touch their existing hook.
- After committing, check `git log -1 --format=%B`. It must be the subject line plus at most two
  sentences, with no attribution. If not, tell the user.
- **no**: stage and commit nothing. Leave files as they are.
- **Never** push, force, amend, rebase or reset. The user pushes.

## Phase 10: Delivery summary (medium/large)

```
For implementer
- Changes: ...
- Upgrade: odoo-bin -u module_name (run on staging first)
- Notes/risks: ...

For customer (UAT)
1. Open ... 2. Do ... 3. You should see ...
```
Customer steps: plain English, no technical words.

---

## Context file (always on)

One file per task: `.claude/context/<task-slug>-context.md`. Create it at the start of any
medium/large task using `references/context-template.md`. After that **only update the same
file**, never create a second one for the same task.

Update it:
- at every checkpoint: research done, questions sent/answered, plan approved, implementation
  done, tests pass, committed;
- whenever the context-guard hook tells you context is at 90% or more (update, then continue);
- right after receiving shell output or a customer/implementer answer.

Keep it a compact summary, not a transcript. Hooks setup: `hooks/README.md`.
