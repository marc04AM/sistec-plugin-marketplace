# blender-ply

Work on **CAD-exported PLY models** (in mm, per-vertex colours, no material) inside
Blender, driven by Claude through the Blender MCP bridge (`mcp__Blender__execute_blender_code`,
port 9876). Each skill runs a bundled Python script **inside Blender** and returns a
JSON report.

## Skills

| Skill | What it does | Changes |
| :---- | :----------- | :------ |
| `/blender-ply:view-ply` | after an import: vertex colours visible, clip computed from the model diagonal, centred 3/4 perspective view, *Zoom to Mouse Position* + *Auto Depth* | view, clip, global zoom preferences, `<Object>_Col` material |
| `/blender-ply:center-blender` | centres the model on its on-screen silhouette; inclination unchanged, zoom backed off only if the model does not fit | the view only |
| `/blender-ply:center-ply` | brings the selected vertex (or the midpoint) to (0,0,0): object origin = 3D cursor = world origin; `dry_run` for a preview | the mesh (undo step "CenterPLY") |
| `/blender-ply:snapshot-ply` | centres and saves a PNG on a white background without overlays (viewport render, view transform `Standard`), then restores | `.png` file; render settings only during the shot |
| `/blender-ply:ply-colors` | restores vertex colours (Solid → `VERTEX`, material for Material Preview); `detect_ply_colors.py` is the read-only version | view, new materials (never existing ones) |

## Hook

| Event | Script | What it does |
| :---- | :----- | :----------- |
| `PostToolUse` on `mcp__Blender__.*` | `hooks/ply-colors-nudge.py` | after a PLY import, or on the first Blender call of the session, queries Blender **read-only** (`detect_ply_colors.py` over socket 9876, 2 s timeout) and warns Claude only if a model with vertex colours is actually shown grey. It fixes nothing: the fix goes through `/blender-ply:ply-colors`. Other calls exit right after a regex. If Blender does not answer it stays silent |

The hook marks the "first call of the session" with a file in
`%TEMP%\claude-blender-ply-colors\`; markers older than 7 days are deleted.

## Optional rule

`rules/blender-ply-colors.md` covers the case the hook cannot see: a model imported
from Blender's UI **after** the session's first MCP call. A plugin cannot
install rules, so anyone who wants it copies it by hand:

```powershell
Copy-Item "<plugin folder>\rules\blender-ply-colors.md" "$env:USERPROFILE\.claude\rules\"
```

Without the rule there is still the `ply-colors` description, which already asks to check the colours on
every scene inspection.

## Requirements

- Blender with the MCP add-on enabled and the server started (Preferences → Add-ons → MCP → Start).
- The Blender MCP server configured in Claude Code (`mcp__Blender__*` tools).
- Blender running **on the same machine** as Claude Code: Blender reads the scripts
  directly from the skill folder (`${CLAUDE_SKILL_DIR}/scripts/…`), so the
  code does not travel through the conversation.

## Notes

- The scripts are idempotent and should be re-run on every turn: the user navigates, imports, enters
  Edit Mode between one call and the next.
- No skill saves the `.blend` or exports the PLY unless the user asks.
- The shared viewport maths (projection, silhouette centring, world-space vertices) lives in
  `lib/view_projection.py` and is used by `center-blender`, `snapshot-ply` and `view-ply`.
  `view-ply` also reuses the `ply-colors` script. The scripts find both starting from their
  own `__file__`, so the plugin structure must be kept.
- The `ply-colors` scripts stay self-contained on purpose: `detect_ply_colors.py` can also be
  sent directly over the bridge socket, where there is no `__file__`.

## Installation

```shell
/plugin install blender-ply@sistec-plugins
```
