import json, sys, os, re

try:
    d = json.load(sys.stdin)
    tool = d.get('tool_name', '')
    cmd = d.get('tool_input', {}).get('command', '')
    is_search = tool in ('Grep', 'Glob') or re.search(r'\b(grep|rg|ripgrep|fd|ack|ag)\b|\bfind ', cmd)
    root = os.environ.get('CLAUDE_PROJECT_DIR', '.')
    if is_search and os.path.exists(os.path.join(root, 'graphify-out', 'graph.json')):
        print(json.dumps({
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'additionalContext': (
                    'graphify: knowledge graph at graphify-out/. '
                    'Run graphify query "<question>" (scoped subgraph) instead of grepping raw files. '
                    'Read GRAPH_REPORT.md only for broad architecture context.'
                )
            }
        }))
except Exception:
    pass
