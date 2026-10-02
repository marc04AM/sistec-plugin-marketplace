---
name: view-ply
description: >-
  ViewPLY — connects to Blender through the MCP bridge, checks that a PLY model has been
  imported, and sets up viewpoint, zoom (clip start/end, zoom to mouse position) and vertex-colour
  display in one go. Use it when the user invokes /blender-ply:view-ply or ViewPLY, and
  whenever they ask to fix, correct or set up the viewpoint, zoom and colours of a PLY in Blender —
  "sistema/correggi/configura il view point, lo zoom e i colori", "ho importato un ply",
  "collegati a Blender e aggiusta la vista", "non vedo il modello", "è tutto grigio", "correggi
  come sempre zoom, viewpoint e colori", "I imported a ply", "fix the view", "I can't see the
  model" — even if the skill is not named. Not for taking a picture of the model (SnapshotPLY)
  or moving the origin (CenterPLY).
---

# ViewPLY

After every import of a CAD PLY into Blender, the same three problems show up:

- **grey model**: the PLY carries the `Col` colour attribute but no material, and Solid view uses the material colour;
- **invisible or clipped model**: models are in mm (thousands of units), while the default `clip_end` is 1000;
- **awkward zoom**: the mouse wheel zooms towards a distant pivot instead of the point under the mouse.

This skill fixes all three in one call and then shows the result. The procedure was repeated in about 12 sessions and is collected here.

## Procedure

1. **Check the bridge.** If a bridge call fails, first check that port 9876 is listening (`Test-NetConnection localhost -Port 9876 -InformationLevel Quiet`). Usually Blender is closed, or the MCP server has not been started (Preferences → Add-ons → MCP → Start). Tell the user so, without guessing further.

2. **Run the script** with `mcp__Blender__execute_blender_code`, using this wrapper. PARAMS is optional: leave it `{}` unless the user asked for something specific.
   ```python
   PARAMS = {}
   p = r"${CLAUDE_SKILL_DIR}/scripts/view_ply.py"
   g = {"PARAMS": PARAMS, "__file__": p}
   exec(compile(open(p, encoding="utf-8").read(), p, "exec"), g)
   result = g["result"]
   ```
   Available parameters:
   - `target`: object name;
   - `elevation_deg`: default 62;
   - `azimuth_deg`: default 40;
   - `margin`: default 1.08;
   - `zoom_prefs`: default True;
   - `colors`: default True.

   The script:
   - finds the meshes that carry a colour attribute;
   - runs the `ply-colors` skill script (it finds it on its own via `__file__`), which sets Solid → `VERTEX` and creates the `<Object>_Col` material;
   - computes the clip range from the model diagonal (`start = diag/2000`, `end = diag*10`);
   - sets a centred 3/4 perspective view, with the distance computed from the lens;
   - turns on *Zoom to Mouse Position* and *Auto Depth*.

   It does not change geometry, selection or object mode. The only shading change is Wireframe → Solid, because no colour can be seen in Wireframe anyway.

3. **Read the report.**
   - `zoom_prefs` gives the final state of the two zoom preferences; `changed` lists only what was changed in this call. If `changed` is empty, the settings were already right.
   - If there is an `error` (no model, object not found), report it and stop. Without an imported PLY there is nothing to set up: ask the user to import it (File → Import → Stanford PLY).
   - `notes` holds cases worth relaying, for example:
     - the PLY has no vertex colours: say so and do not invent colours;
     - the object is in Edit Mode;
     - an existing material does not read the colour attribute;
     - "Colour script not found": the plugin is installed incompletely.

4. **Check with a screenshot**: `mcp__Blender__get_screenshot_of_window_as_image` with `size_limit_in_bytes: 400000` (without this parameter the call fails). The model must be whole, centred and coloured. If the screenshot is black, the Blender window is minimised: ask the user to restore it.

5. **Answer briefly**: what was set, plus at most one question. For example: "Model `X` (1476×2916×4148 mm): colours on (3 tints), clip 2.6 → 52,000, centred 3/4 view, zoom to mouse on." The user prefers short answers, without tables or a description of the method. Answer in the user's language.

## Things to know

- **The scene changes between turns**: the user imports other models, rotates the view, enters Edit Mode. Re-run the script every time instead of reusing old numbers.
- **A clip range that is too wide is as harmful as one that is too narrow.** With `clip_end` 490,000 on CorpoPressa, white streaks (z-fighting) appeared that looked like mesh defects. With a `clip_start` of 1–1.6 it was impossible to get close to the details. If the user wants to zoom in very close on a large part, lower `clip_start` (for example 0.05) but also reduce `clip_end`.
- **Frame Selected (numpad `.`, which is `,` on the Italian keyboard) does not change the clip range**: that is why the script sets it first.
- **Colours are lost on every re-import**, because the material is created with the object. Suggest saving the `.blend`, or File → Defaults → Save Startup File to keep the view settings. Save the `.blend` only if the user asks.
- **The zoom preferences are global**, and Blender saves them on its own if preference auto-save is on. Mention them in the answer, so the user knows they changed.
- **Manual procedure, to explain if the user asks.** Shading menu at the top right → Color → Attribute (the UI label for `VERTEX`). Sidebar N → View → Clip Start/End. Edit → Preferences → Navigation → Zoom to Mouse Position and Auto Depth.
- **Object far from the origin**: if the model shows up as a dot, the script frames it anyway, because it centres on the world-space bounding box.
- To move the origin use **CenterPLY**; to save an image use **SnapshotPLY**.
