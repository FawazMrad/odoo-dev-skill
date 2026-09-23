# Context hooks

`install.py` registers these automatically. Manual setup is only needed if you skip it.

| Hook | Script | What it does |
|---|---|---|
| `Stop` | `context_guard.py` | After each reply, reads real token usage from the session transcript. At 90%+ it tells Claude to update the current task context file in place. Fires again only after ~4% more growth. |
| `SessionStart` (startup, resume, compact) | `session_restore.py` | Lists task context files. After compaction or resume, injects the newest file so Claude continues from "Next steps". |
| `PreCompact` | `pre_compact_stamp.py` | Stamps "Last compaction" in the newest context file. |

All three do nothing in projects without `.claude/context/` (created by the skill on medium/large tasks).

## Settings

Environment variables (optional, e.g. in `settings.json` → `env`):

- `ODOO_CONTEXT_WINDOW` window size in tokens, default `200000`. Set `1000000` if you use a 1M context model.
- `ODOO_CONTEXT_THRESHOLD` default `0.90`.
- `ODOO_CONTEXT_STEP` extra growth before firing again, default `0.04`.

## Manual settings.json block (personal install)

```json
{
  "hooks": {
    "Stop": [{ "hooks": [{ "type": "command", "command": "python3 \"$HOME/.claude/skills/odoo-dev/hooks/context_guard.py\"" }] }],
    "SessionStart": [{ "matcher": "startup|resume|compact", "hooks": [{ "type": "command", "command": "python3 \"$HOME/.claude/skills/odoo-dev/hooks/session_restore.py\"" }] }],
    "PreCompact": [{ "hooks": [{ "type": "command", "command": "python3 \"$HOME/.claude/skills/odoo-dev/hooks/pre_compact_stamp.py\"" }] }]
  }
}
```
Check with `/hooks` inside Claude Code.
