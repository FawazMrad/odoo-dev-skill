#!/usr/bin/env python3
"""PreCompact hook: stamp the newest task context file so we know a compaction happened."""
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import context_files, read_input  # noqa: E402


def main():
    data = read_input()
    files = context_files(data)
    if not files:
        return
    latest = files[0]
    text = latest.read_text(encoding='utf-8', errors='ignore')
    stamp = f"- Last compaction: {datetime.now():%Y-%m-%d %H:%M} ({data.get('trigger', 'auto')})"
    if re.search(r'^- Last compaction:.*$', text, flags=re.M):
        text = re.sub(r'^- Last compaction:.*$', stamp, text, count=1, flags=re.M)
    else:
        lines = text.splitlines()
        # put it under the title block
        idx = 1 if lines and lines[0].startswith('#') else 0
        lines.insert(idx + 1, stamp)
        text = '\n'.join(lines) + '\n'
    latest.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
