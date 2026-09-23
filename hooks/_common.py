import json
import os
import sys
from pathlib import Path


def read_input():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def project_dir(data):
    return Path(os.environ.get('CLAUDE_PROJECT_DIR') or data.get('cwd') or os.getcwd())


def context_dir(data):
    return project_dir(data) / '.claude' / 'context'


def context_files(data):
    d = context_dir(data)
    if not d.is_dir():
        return []
    files = [p for p in d.glob('*-context.md') if p.is_file()]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
