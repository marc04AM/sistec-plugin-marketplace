import json, os, glob

try:
    root = os.environ.get('CLAUDE_PROJECT_DIR', '.')
    archive = os.path.join(root, '.claude', 'claude-archive')
    files = sorted(
        glob.glob(os.path.join(archive, '*.md')),
        key=os.path.getmtime,
        reverse=True,
    )[:5]
    entries = []
    for f in files:
        title = os.path.basename(f)
        try:
            with open(f, encoding='utf-8') as fh:
                for line in fh:
                    if line.startswith('# '):
                        title = line[2:].strip()
                        break
        except Exception:
            pass
        entries.append('- ' + title)
    if entries:
        print(json.dumps({
            'hookSpecificOutput': {
                'hookEventName': 'SessionStart',
                'additionalContext': (
                    'Recent claude-archive change history '
                    '(recall before re-deriving past decisions):\n' + '\n'.join(entries)
                )
            }
        }))
except Exception:
    pass
