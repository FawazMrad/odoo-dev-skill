#!/usr/bin/env python3
"""Install the commit-msg hook that strips AI attribution into a git repo.

  python3 install_git_hook.py [repo_path]     # default: current folder

Won't overwrite a different commit-msg hook that already exists.
"""
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

MARK = 'odoo-dev: strip AI attribution'


def main():
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    try:
        hooks_dir = subprocess.run(
            ['git', 'rev-parse', '--git-path', 'hooks'], cwd=repo,
            capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit(f'Not a git repo: {repo}')
    hooks = (repo / hooks_dir).resolve()
    hooks.mkdir(parents=True, exist_ok=True)
    target = hooks / 'commit-msg'
    src = Path(__file__).with_name('commit-msg')

    if target.exists():
        if MARK in target.read_text(errors='ignore'):
            print(f'OK: hook already installed ({target})')
            return
        sys.exit(f'STOP: a different commit-msg hook exists at {target}. Ask the user before changing it.')

    shutil.copyfile(src, target)
    # keep unix line endings, git bash on windows chokes on CRLF
    target.write_bytes(target.read_bytes().replace(b'\r\n', b'\n'))
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f'Installed: {target}')


if __name__ == '__main__':
    main()
