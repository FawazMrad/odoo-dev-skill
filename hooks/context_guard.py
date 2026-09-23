#!/usr/bin/env python3
"""Stop hook: when context usage is >= threshold, ask Claude to update the task context file."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import context_dir, read_input  # noqa: E402

WINDOW = int(os.environ.get('ODOO_CONTEXT_WINDOW', '200000'))
THRESHOLD = float(os.environ.get('ODOO_CONTEXT_THRESHOLD', '0.90'))
# fire again only after this much more growth, so it doesn't nag every turn
STEP = float(os.environ.get('ODOO_CONTEXT_STEP', '0.04'))


def last_usage_tokens(transcript):
    try:
        lines = Path(transcript).read_text(encoding='utf-8', errors='ignore').splitlines()
    except Exception:
        return 0
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except Exception:
            continue
        usage = (entry.get('message') or {}).get('usage') if isinstance(entry, dict) else None
        if usage:
            return sum(int(usage.get(k) or 0) for k in (
                'input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens'))
    return 0


def main():
    data = read_input()
    # already continuing because of a hook, don't loop
    if data.get('stop_hook_active'):
        return
    cdir = context_dir(data)
    # only active in projects where the skill started a context file
    if not cdir.is_dir():
        return
    tokens = last_usage_tokens(data.get('transcript_path') or '')
    if not tokens:
        return
    ratio = tokens / WINDOW
    state_file = cdir / f".guard-{data.get('session_id', 'default')}.json"
    try:
        last = json.loads(state_file.read_text()).get('ratio', 0)
    except Exception:
        last = 0
    if ratio < THRESHOLD:
        if last:  # dropped below again (compaction), reset
            state_file.write_text(json.dumps({'ratio': 0}))
        return
    if last and ratio < last + STEP:
        return
    state_file.write_text(json.dumps({'ratio': ratio}))
    print(json.dumps({
        'decision': 'block',
        'reason': (
            f'Context window is at about {ratio:.0%}. Update the CURRENT task context file in '
            '.claude/context/ in place (do not create a new file): findings, decisions, open '
            'questions, files changed, status, next steps. Then say one line "Context file updated" '
            'and stop.'
        ),
    }))


if __name__ == '__main__':
    main()
