#!/usr/bin/env python3
"""SessionStart hook: point Claude to existing task context files (full content after compaction)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import context_files, read_input  # noqa: E402

MAX_CHARS = 12000


def main():
    data = read_input()
    files = context_files(data)
    if not files:
        return
    source = data.get('source', '')
    out = ['[odoo-dev] Task context files in .claude/context/ (newest first):']
    for p in files[:10]:
        age_h = (time.time() - p.stat().st_mtime) / 3600
        out.append(f'- {p.name} (updated {age_h:.0f}h ago)')
    if source in ('compact', 'resume'):
        latest = files[0]
        text = latest.read_text(encoding='utf-8', errors='ignore')[:MAX_CHARS]
        out += ['', f'Session was {"compacted" if source == "compact" else "resumed"}. Latest task file ({latest.name}):', '', text,
                '', 'Continue from its "Next steps". Keep updating this same file.']
    else:
        out.append('If the user continues one of these tasks, read that file first.')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
