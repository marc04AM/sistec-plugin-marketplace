---
name: ply-colors
description: >-
  Restore vertex-colour display for PLY models in Blender via the Blender MCP bridge. PLY files
  carry per-vertex colours but no materials, and Blender's Solid viewport defaults to material
  colour, so imported models render as flat default grey and the colours look lost even though
  they are in the file. Use this skill right after any .ply is imported into Blender, and whenever
  a Blender model looks grey, washed out or colourless, or the user asks why colours are missing
  or wrong — "non vedo i colori", "è tutto grigio", "i colori del PLY non si vedono", "perché è
  grigio", "why is my model grey", "vertex colors not showing", "the import lost its colors". Also
  run it as a routine check after importing a PLY even when the user says nothing about colours,
  since they usually only notice the grey later — whenever inspecting or modifying a Blender scene
  via MCP, treat colour display as part of the inspection. For the full post-import setup (view, clip,
  zoom and colours together) use /blender-ply:visualizzaply, which already runs this script.
---

# Restoring PLY vertex colours in Blender

## Why models go grey

A PLY exported from a CAD or scanning tool stores colour per vertex, typically as
`uchar red/green/blue/alpha`. Blender's importer turns that into a **colour
attribute** on the mesh (commonly named `Col`), and stops there — PLY has no
concept of a material, so the object arrives with **zero material slots**.

That is the whole problem. Blender's Solid viewport paints surfaces according to
Viewport Shading → Color, which defaults to `MATERIAL`. With no material to read,
it falls back to the default grey and ignores the colour attribute completely.
The colours are in the mesh the entire time; nothing is drawing them.

This matters for how you talk about it: the colours were never lost, and no
import setting was wrong. Say that plainly rather than implying data was damaged.

Material Preview and Rendered ignore the Solid colour setting entirely, so they
stay grey for a different reason — they need a real material that routes the
colour attribute into Base Color. Fixing only one of the two leaves the user
confused when they switch shading mode, so handle both.

## Doing it

Run `scripts/restore_ply_colors.py` with `mcp__Blender__execute_blender_code`, using
this wrapper (Blender reads the file from disk, so the script does not travel through
the conversation):

```python
p = r"${CLAUDE_SKILL_DIR}/scripts/restore_ply_colors.py"
g = {"__file__": p}
exec(compile(open(p, encoding="utf-8").read(), p, "exec"), g)
result = g["result"]
```

It resolves both causes in one pass and returns a JSON summary.

The script is idempotent, so run it freely — right after an import, when a model
looks grey, or just to check. When everything is already correct it reports
`"changed": false` and touches nothing.

`scripts/detect_ply_colors.py` is the read-only counterpart (same wrapper, other
file name): it answers "is anything actually grey right now?" without changing a
thing. Reach for it when you want to report state without acting, or to re-check a
claim.

If the bridge does not answer, check that port 9876 has a listener before
guessing at anything else; Blender may simply have been closed.

Do not improvise the fix from memory: the viewport enum name is version-dependent
(`VERTEX` or `ATTRIBUTE`) and the script resolves it at runtime.

## How this skill gets invoked

Three layers point here, each covering a different blind spot — worth knowing so
you can tell whether one has failed:

- The plugin hook `hooks/ply-colors-nudge.py` runs after every Blender MCP call.
  On a PLY import, or on the first Blender call of a session, it runs
  `detect_ply_colors.py` read-only over the bridge socket. It only speaks when
  something is measurably grey — so if it spoke, the problem is real and
  asserting the scene looks fine is wrong. Re-run the detection instead of
  overriding it. Any other call costs one regex and exits.
- The optional rule `rules/blender-ply-colors.md` (copied by hand into
  `~/.claude/rules/`, see the plugin README) is the backstop for what the hook
  cannot observe: a model imported in Blender's own UI after the session's first
  Blender call. Without it, this description is that backstop.
- This skill holds the procedure, so none of the above has to.

## Reading the report

- `viewports[].color_type_before/after` — the Solid shading fix. Going from
  `MATERIAL` to `VERTEX` is the change that makes colours appear.
- `objects[].action` — `created-material` means the object had no material and
  got one named `<Object>_<Attribute>`. `kept-existing-material` means it already
  had one and was left alone.
- `objects[].reads_color_attribute` — for objects that already had a material,
  whether that material actually reads the colour attribute. When `false`, the
  model will stay grey in Material Preview; report it and ask before touching a
  material you did not create.
- `notes` — conditions worth relaying, such as a viewport sitting in Wireframe
  (nothing shows there regardless) or no colour attribute existing at all.

If no mesh carries a colour attribute, the file genuinely has no vertex colours.
Say so instead of inventing a material to fill the gap — a fabricated colour is
worse than an honest grey, because the user may believe it came from their data.

## Things worth getting right

This script never changes the viewport **shading mode** (Solid / Material Preview
/ Rendered). That is the user's own view preference, and silently switching it is
disorienting. It only changes what Solid mode uses as its colour source.
(/blender-ply:visualizzaply is the one exception: it moves a Wireframe viewport to
Solid, because no colour can be seen in Wireframe at all.)

It also never overwrites an existing material, because a material the user built
carries intent the script cannot see.

Materials are named `<ObjectName>_<AttributeName>` to stay findable and to match
the naming already in the file. If the project has its own convention, follow
that instead.

Adding a material changes nothing about the geometry, and PLY export ignores
materials entirely — so a subsequent re-export is unaffected. Mention this when
the user is mid-edit and might worry the fix contaminates their output file.

## Confirming it worked

Vertex colours are exactly the kind of thing worth showing rather than asserting.
Take a screenshot with `mcp__Blender__get_screenshot_of_window_as_image` (pass
`size_limit_in_bytes: 400000`) and check the model is no longer uniform grey.

To state the actual palette rather than guessing at it, read the colours straight
from the mesh, or from the PLY on disk when you want to prove the file and the
viewport agree:

```python
import bpy
from collections import Counter
me = bpy.data.objects["<name>"].data
attr = me.color_attributes.active_color
counts = Counter(
    tuple(round(c, 4) for c in d.color) for d in attr.data
)
result = {"distinct": len(counts), "top": counts.most_common(8)}
```

Note that colour attributes are stored **linear**, while the PLY on disk holds
sRGB bytes — so the two sets of numbers will not match digit for digit even when
they are the same colours. Convert before comparing, or compare only counts.

## A related trap when exporting

If the user later asks for the edited mesh back as PLY, Blender's exporter
round-trips colours through `uchar sRGB → linear float → uchar sRGB` and can
shift channels by ±1 on most vertices. It is invisible, but it alters data the
user did not ask to change. For a purely subtractive edit (deleting geometry),
rewriting the original file's records directly is byte-exact and avoids the
drift. Worth flagging when colour fidelity matters.
