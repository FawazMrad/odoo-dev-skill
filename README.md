# odoo-dev

A Claude Code skill for Odoo development (16, 17, 18, 19 / community, enterprise, Odoo.sh).

It makes Claude read the real Odoo source before coding, check what else touches the same
model or view, ask the right person when something is unclear, write real tests, review its own
work through a second agent, and commit the way we commit. Its main job is to **not break
existing modules or lose data**.

## Install

```bash
git clone <this-repo-url> ~/.claude/skills/odoo-dev
python3 ~/.claude/skills/odoo-dev/install.py          # windows: python
```
Restart Claude Code (or VS Code). The installer:
- copies the skill to `~/.claude/skills/odoo-dev`
- installs the `odoo-reviewer` agent to `~/.claude/agents`
- registers the 3 context hooks and turns commit attribution off in `~/.claude/settings.json`
  (a backup is made first)
- finds your local Odoo community/enterprise folders once and saves them

Per-repo install instead (whole team gets it from git):
```bash
python3 ~/.claude/skills/odoo-dev/install.py --project /path/to/repo
# then commit .claude/skills, .claude/agents, .claude/settings.json
```

Update:
```bash
cd ~/.claude/skills/odoo-dev && git pull && python3 install.py
```

If you use a 1M-context model, add to `~/.claude/settings.json`:
```json
"env": { "ODOO_CONTEXT_WINDOW": "1000000" }
```

## Use

Just describe the task in an Odoo repo. The skill triggers by itself:
```
in grace_quotation_report, add the delivery date under the customer address
```
Force it with `/odoo-dev <task>` when the request doesn't sound like Odoo work.

It's working if the first reply states the Odoo version and a size line, e.g.
`Size: medium (new computed field on sale.order, 2 files)`.

## The rules it follows

**Before coding**
- Detects the Odoo version from the manifest, then applies that version's syntax
  (`attrs` vs expressions, `tree` vs `list`, `name_get` vs `_compute_display_name`,
  `_sql_constraints` vs `models.Constraint`).
- Greps your local community **and** enterprise source, plus the repo, for everything that
  touches the same model, view or method. Core folders are read-only reference.
- Sizes the task (small / medium / large) and runs only what that size needs. You can override.
- Unclear points get routed: business questions → a draft message to the **customer**, scope
  questions → the **implementer**, core behavior → it reads the source, instance facts
  (Studio fields, automations, data) → a **read-only** `odoo-bin shell` script for you to run.
- Reports and custom UIs: it asks for layout, fields, totals and branding instead of inventing.
- Medium/large tasks get a short plan for approval before any code.

**Data and compatibility safety**
- Extend with `_inherit`, never redefine an existing model.
- No field type changes; no `required=True` without a default **and** a migration; renames and
  data moves need a migration script; removing a field needs your confirmation.
- Every override calls `super()` and returns its result, with the original signature.
- xpath anchored on `name`; `position="replace"` on core only with a reason and `priority > 100`.
- Checks which other views inherit the same view before touching it.
- Only the task's module is edited.

**Code**
- Clean and idiomatic for the version, short human comments that say *why*.
- `_logger`, never `print`. No secrets. No hardcoded IDs (`env.ref(...)`).
- No N+1 queries; batching, `mapped`/`filtered`/`read_group`, correct `@api.depends`,
  `index=True` where it's searched, a warning before stored computes on big tables.
- Multi-record `self`, multi-company, currency handling.
- Access rows and record rules for new models; `sudo()` only with a reason.
- Config data in `<data noupdate="1">` so upgrades don't overwrite client settings.
- Manifest: version bump, complete `depends`, load order, license. External libs in
  `requirements.txt` + `external_dependencies`.
- OCA conventions (see `references/oca-guidelines.md`): model attribute order, method/field
  naming, import order, no raw SQL, never `cr.commit()`, hooks in `hooks.py`, semantic version
  bumps. Naming conventions for XML IDs / files / modules are **opt-in**: it follows whatever
  the repo already does.

**Tests**
- Scaled to task size: happy path, edge cases, multi-record, access rights as a non-admin,
  multi-company, constraints, regression of the core flow touched, computes, report rendering.
- `freeze_time` for dates, mocks for external services, no demo data, no live DB.
- Actually run, with the real result reported.

**Review**
- Self-review first: compile, XML validity, lint if installed, diff scan for debug code.
- Then the read-only `odoo-reviewer` agent, which has **veto**: a `BLOCKED` verdict must be
  fixed and re-reviewed before you're asked to commit.
- Parallel subagents are used for research and test writing only. Code stays on one branch,
  one database, one commit flow.

**Git**
- Appends to `.gitignore`: `__pycache__/`, `*.py[cod]`, `README*`, `CLAUDE.md`,
  `.claude/context/`, `.claude/settings.local.json`, `*context*.md`.
- Asks **Commit this? (yes/no)** when the task is done.
- On yes: stages only the task's files (never `git add -A`), one commit per module:
  ```
  [TAG] - module_name. short brief.
  ```
  Tags: `ADD`, `UPDATE`, `IMP`, `FIX`, `REMOVE`, `REF`, `MIG`, `PERF`, `TEST`.
  A body is allowed only when the subject isn't enough: at most two plain sentences. No bullets,
  no sections, no changelog.
- **No AI attribution anywhere.** Disabled in settings, forbidden in the skill, and stripped by
  a `commit-msg` git hook installed per repo:
  ```bash
  python3 ~/.claude/skills/odoo-dev/scripts/install_git_hook.py /path/to/repo
  ```
- On no: nothing staged or committed.
- It never pushes, forces, amends, rebases or resets. You push.

**Odoo.sh**
- Shell scripts are read-only, staging by default, production only if you say so.
- It never installs, upgrades or uninstalls on the instance; it gives you the command.

**Delivery**
- A short technical note for the implementer (changes, upgrade command, risks) and plain-English
  UAT steps for the customer.

**If you ask it to break a rule** (skip tests, push, replace a core view), it says which rule and
what the risk is, asks once, then follows your call.

## Context across long sessions

Medium/large tasks get `.claude/context/<task>-context.md`, updated in place at every checkpoint
and whenever context passes 90%. After a compaction or `--resume`, the file is injected back and
work continues from "Next steps". Start a new session and say "continue the X task" and it picks
up from there.

## Odoo source paths

Found once and saved to `~/.claude/odoo-paths.json`; searched again only if a saved folder moved.

```bash
python3 scripts/find_odoo.py            # show everything saved
python3 scripts/find_odoo.py 17.0       # one version
python3 scripts/find_odoo.py --set 16.0 community=/path/odoo enterprise=/path/enterprise
python3 scripts/find_odoo.py --rescan   # force a fresh search
```
Sources outside the searched roots: `export ODOO_SEARCH_ROOTS=/your/dir` (Windows: `;` separated).

## Layout

```
SKILL.md                    the workflow (phases 0-10)
agents/odoo-reviewer.md     read-only reviewer with veto
references/
  version-notes.md          16 → 19 differences
  safe-inheritance.md       model/view/data safety checklist
  testing.md                test standard per task size
  shell-recipes.md          read-only odoo-bin shell scripts
  oca-guidelines.md         OCA / Odoo conventions
  context-template.md       task context file shape
scripts/
  find_odoo.py              locate + cache Odoo source paths
  install_git_hook.py       install the commit-msg hook in a repo
  commit-msg                the hook itself
hooks/                      context guard, session restore, pre-compact stamp
install.py                  installer
```

## Notes

- Nothing personal is stored in this repo: your paths live in `~/.claude/odoo-paths.json`, your
  settings in `~/.claude/settings.json`, task context inside each project repo.
- Windows, macOS and Linux all work. On Windows use `python` if `python3` isn't found.
- Requires Python 3.8+ and git.
