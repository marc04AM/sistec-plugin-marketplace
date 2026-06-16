import json, sys

try:
    d = json.load(sys.stdin)
    path = d.get('tool_input', {}).get('file_path', '')
    if path and path.endswith('.cs'):
        print(json.dumps({
            'hookSpecificOutput': {
                'hookEventName': 'PostToolUse',
                'additionalContext': (
                    'Workflow: run dotnet build after editing .cs files '
                    'in Communication or Business Logic layers (per workflow.md).'
                )
            }
        }))
except Exception:
    pass
