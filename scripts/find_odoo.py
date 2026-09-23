#!/usr/bin/env python3
"""Find local Odoo community/enterprise source folders per version.

  python3 find_odoo.py 17.0        # paths for one version
  python3 find_odoo.py             # everything found
  python3 find_odoo.py --rescan    # ignore cache

Searches once and saves to ~/.claude/odoo-paths.json. Later runs only check that the
saved folders still exist; it searches again only when they're gone (or the version was
never found). Save paths by hand:  python3 find_odoo.py --set 17.0 community=/p enterprise=/p
Extra roots: ODOO_SEARCH_ROOTS (separated by ":" on Linux/macOS, ";" on Windows).
"""
import json
import os
import re
import sys
from pathlib import Path

CACHE = Path.home() / '.claude' / 'odoo-paths.json'
MAX_DEPTH = 6
SKIP = {'node_modules', '.git', '__pycache__', '.cache', '.npm', '.local', 'proc', 'sys',
        'dev', 'snap', 'Library', 'filestore', 'sessions', '.venv', 'venv', 'site-packages',
        # windows
        'Windows', 'AppData', 'ProgramData', '$Recycle.Bin', 'System Volume Information',
        'Microsoft', 'WindowsApps', 'Recovery', 'PerfLogs'}


def roots():
    """(folder, max depth) pairs to search."""
    extra = [p for p in os.environ.get('ODOO_SEARCH_ROOTS', '').split(os.pathsep) if p]
    found = [(p, MAX_DEPTH) for p in extra]
    found.append((str(Path.home()), MAX_DEPTH))
    if os.name == 'nt':
        # windows: odoo often lives right under a drive (C:\odoo, D:\work) or Program Files
        for letter in 'CDEFG':
            drive = f'{letter}:\\'
            if os.path.isdir(drive):
                found.append((drive, 4))
    else:
        for p in ('/opt', '/srv', '/var/lib', '/usr/local/src', '/workspace', '/code'):
            found.append((p, MAX_DEPTH))
    return [(p, d) for p, d in found if os.path.isdir(p)]


def community_version(root):
    rel = Path(root) / 'odoo' / 'release.py'
    try:
        m = re.search(r'version_info\s*=\s*\((\d+)\s*,\s*(\d+)', rel.read_text(errors='ignore'))
    except OSError:
        return None
    if not m:
        return None
    major, minor = m.groups()
    return f'{major}.{minor}'


def git_branch_version(root):
    head = Path(root) / '.git' / 'HEAD'
    try:
        ref = head.read_text().strip()
    except OSError:
        return None
    m = re.search(r'(?:saas-)?(\d+\.\d+)\s*$', ref)
    return m.group(1) if m else None


def scan():
    communities, enterprises, seen = [], [], set()
    for base, max_depth in roots():
        base_depth = len(Path(base).parts)
        for cur, dirs, files in os.walk(base, followlinks=False):
            key = os.path.normcase(os.path.abspath(cur))
            if key in seen:  # home is also inside C:\\, don't walk it twice
                dirs[:] = []
                continue
            seen.add(key)
            if len(Path(cur).parts) - base_depth >= max_depth:
                dirs[:] = []
            dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith('.')]
            if 'odoo-bin' in files and os.path.isfile(os.path.join(cur, 'odoo', 'release.py')):
                communities.append(cur)
                dirs[:] = []  # don't walk into the source tree
            elif 'web_enterprise' in dirs and os.path.isfile(os.path.join(cur, 'web_enterprise', '__manifest__.py')):
                enterprises.append(cur)
                dirs[:] = []
    return communities, enterprises


def build(communities, enterprises):
    result = {}
    for c in communities:
        v = community_version(c)
        if not v:
            continue
        entry = result.setdefault(v, {'community': [], 'enterprise': []})
        if c not in entry['community']:
            entry['community'].append(c)
    for e in enterprises:
        v = git_branch_version(e)
        if not v:
            # no git info: take the version of a community folder next to it
            parent = str(Path(e).parent)
            v = next((community_version(c) for c in communities if str(Path(c).parent) == parent), None)
        entry = result.setdefault(v or 'unknown', {'community': [], 'enterprise': []})
        if e not in entry['enterprise']:
            entry['enterprise'].append(e)
    for v, entry in result.items():
        entry['addons'] = [p for c in entry['community']
                           for p in (os.path.join(c, 'addons'), os.path.join(c, 'odoo', 'addons')) if os.path.isdir(p)]
    return result


def version_valid(entry):
    comm = entry.get('community', [])
    ent = entry.get('enterprise', [])
    if not comm and not ent:
        return False
    return all(os.path.isfile(os.path.join(p, 'odoo', 'release.py')) for p in comm) and \
        all(os.path.isfile(os.path.join(p, 'web_enterprise', '__manifest__.py')) for p in ent)


def load():
    try:
        return json.loads(CACHE.read_text())
    except Exception:
        return {}


def save(data):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, indent=2))


def rescan_into(data):
    found = build(*scan())
    # only replace versions that are broken or new, keep the rest as saved
    for v, entry in found.items():
        if v not in data or not version_valid(data[v]):
            data[v] = entry
    return data


def set_paths(version, pairs):
    data = load()
    entry = data.get(version) or {'community': [], 'enterprise': []}
    for pair in pairs:
        key, _, path = pair.partition('=')
        path = str(Path(path).expanduser().resolve())
        if key not in ('community', 'enterprise'):
            sys.exit(f'unknown key {key}, use community= or enterprise=')
        entry[key] = [path]
    entry['addons'] = [p for c in entry['community']
                       for p in (os.path.join(c, 'addons'), os.path.join(c, 'odoo', 'addons')) if os.path.isdir(p)]
    entry['source'] = 'user'
    data[version] = entry
    save(data)
    return entry


def main():
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    args = [a for a in sys.argv[1:] if not a.startswith('--')]

    if '--set' in flags:
        # find_odoo.py --set 17.0 community=/path enterprise=/path
        entry = set_paths(args[0], args[1:])
        print(json.dumps({'version': args[0], 'saved': True, **entry}, indent=2))
        return

    want = args[0] if args else None
    data = load()
    scanned = False

    if '--rescan' in flags or not data:
        # first run (or forced): search once and save
        data = rescan_into({} if '--rescan' in flags else data)
        scanned = True
    elif want and (want not in data or not version_valid(data[want])):
        # saved paths are gone or version unknown: search again, once
        data = rescan_into(data)
        scanned = True

    if scanned:
        save(data)

    if not want:
        print(json.dumps(data, indent=2))
        return
    entry = data.get(want)
    if not entry or not version_valid(entry):
        print(json.dumps({
            'version': want, 'found': False, 'available': sorted(data),
            'hint': f'Ask the user for the paths, then save them: find_odoo.py --set {want} '
                    'community=/path enterprise=/path',
        }, indent=2))
        sys.exit(1)
    print(json.dumps({'version': want, 'found': True, 'from_cache': not scanned, **entry,
                      'enterprise_missing': not entry['enterprise']}, indent=2))


if __name__ == '__main__':
    main()
