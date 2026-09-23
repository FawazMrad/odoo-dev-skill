#!/usr/bin/env python3
"""Install the odoo-dev skill and its context hooks for Claude Code.

  python3 install.py                 # personal: ~/.claude (all projects)
  python3 install.py --project PATH  # one repo: PATH/.claude (share with the team via git)

Safe to run again. settings.json is backed up before any change.
"""
import argparse
import json
import subprocess
import sys
import os
import shutil
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent
NAME = 'odoo-dev'


def hook_cmd(dest, script):
    # absolute python + script path: no python3/$HOME differences between windows and linux
    py = Path(sys.executable).as_posix()
    target = (dest / 'hooks' / script).as_posix()
    return f'"{py}" "{target}"'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project', help='repo root to install into instead of ~/.claude')
    args = ap.parse_args()

    if args.project:
        root = Path(args.project).expanduser().resolve() / '.claude'
        settings = root / 'settings.json'
    else:
        root = Path.home() / '.claude'
        settings = root / 'settings.json'

    dest = root / 'skills' / NAME
    if dest.resolve() != SRC:
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(SRC, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.zip'))
    print(f'Skill installed: {dest}')

    # review subagent
    agents = root / 'agents'
    agents.mkdir(parents=True, exist_ok=True)
    for a in (SRC / 'agents').glob('*.md'):
        shutil.copy2(a, agents / a.name)
        print(f'Agent installed: {agents / a.name}')

    wanted = {
        'Stop': [{'hooks': [{'type': 'command', 'command': hook_cmd(dest, 'context_guard.py')}]}],
        'SessionStart': [{'matcher': 'startup|resume|compact',
                          'hooks': [{'type': 'command', 'command': hook_cmd(dest, 'session_restore.py')}]}],
        'PreCompact': [{'hooks': [{'type': 'command', 'command': hook_cmd(dest, 'pre_compact_stamp.py')}]}],
    }

    data = {}
    if settings.exists():
        backup = settings.with_name(f'settings.json.bak-{time.strftime("%Y%m%d%H%M%S")}')
        shutil.copy2(settings, backup)
        print(f'Backup: {backup}')
        data = json.loads(settings.read_text() or '{}')
    # no Claude attribution in commits or PRs
    data['attribution'] = {'commit': '', 'pr': ''}
    data['includeCoAuthoredBy'] = False
    hooks = data.setdefault('hooks', {})
    for event, groups in wanted.items():
        existing = hooks.setdefault(event, [])
        present = {h.get('command') for grp in existing for h in grp.get('hooks', [])}
        for g in groups:
            if g['hooks'][0]['command'] not in present:
                existing.append(g)
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(data, indent=2) + '\n')
    print(f'Hooks registered and commit attribution disabled in: {settings}')
    print('Checking local Odoo sources...')
    subprocess.run([sys.executable, str(dest / 'scripts' / 'find_odoo.py')])
    print('Done. Restart Claude Code.')


if __name__ == '__main__':
    main()
