---
name: fotografaply
description: >-
  FotografaPLY — centres the PLY model on Blender's screen keeping the inclination (and zoom) the
  user already set, makes the background white, removes grid, axes, overlays and gizmos, and saves
  a clean PNG of the model through a viewport render; then restores the view as it was. Use it
  when the user invokes /blender-ply:fotografaply or FotografaPLY, and whenever they ask for a
  picture of a model in Blender — "fai una foto/uno screenshot/un'immagine/un render del
  modello", "salva un'immagine con sfondo bianco", "togli la griglia e salva il png", "centra e
  fotografa", "immagine per il manuale/documento", "take a picture of the model", "save a PNG with
  white background" — even if the skill is not named. Not for fixing view and colours after an
  import (VisualizzaPLY).
---

# FotografaPLY

Produces an image of the model as the user sees it in the viewport: same vertex colours, same inclination, but **centred**, on a **white background** and **without grid, axes, selection outlines or gizmos**.

The recipe was worked out in the grippers session (10 images `pinza_XX_viewport.png`).

## Procedure

1. **Let the user set up the framing.** The inclination (and usually the zoom) is their call. If the model has just been imported and is grey or invisible, run **VisualizzaPLY** first.

2. **Run the script** with `mcp__Blender__execute_blender_code`:
   ```python
   PARAMS = {}
   p = r"${CLAUDE_SKILL_DIR}/scripts/fotografa_ply.py"
   g = {"PARAMS": PARAMS, "__file__": p}
   exec(compile(open(p, encoding="utf-8").read(), p, "exec"), g)
   result = g["result"]
   ```
   Useful parameters:
   - `output`: full path of the `.png`. Default is `<.blend folder>/<object>_viewport.png`, with a `_2`, `_3`… suffix if the file already exists.
   - `target`: object to photograph.
   - `isolate=True`: hides the other objects for the shot only.
   - `fit=True` (with `fill`, default 0.9): also adjusts the zoom. Use it only if the user asks or if the model goes out of frame.
   - `width`: default 2400 px; the height follows the viewport proportions.
   - `restore=False`: leaves the view in photo style.
   - `overwrite=True`: overwrites the existing file.

   Centring and the shot happen **in the same call**, on purpose. The user moves the view between turns, and a shot fired separately would catch a different framing.

3. **Read the report.**
   - `image`: saved path; `exists`: confirms the file was written.
   - `frame_fill`: how much of the frame the model takes up (1.0 = touches the edge).
   - `notes`: for example the model going out of frame, or part of the model behind the viewpoint.
   - If there is an `error` because the `.blend` is not saved, ask the user where to save the image. Do not pick a folder outside the working one yourself.

4. **Check the image**: read it with Read and check that the background is true white rather than grey, and that the model is whole and centred. If the environment has a tool for sending files to the user (for example SendUserFile), use it; otherwise the path is enough.

5. **Answer briefly**, in the user's language: file path, size and any question. For example: "Saved `pinza_05_viewport.png` (2400×1354). Move on to the next one?"

## Why it works this way

- **Viewport render, not scene render.** `bpy.ops.render.opengl(write_still=True, view_context=True)` inside a `temp_override` on the 3D view needs no camera or lights, and reproduces the Solid colours exactly as they are seen. In the UI it is View → Viewport Render Image, then Image → Save As: on its own it saves nothing.
- **Standard instead of AgX.** The render goes through the scene's colour management: with AgX (the default) pure white comes out grey, about #c8c8c8, even though it looks white in the viewport. The script sets `view_transform='Standard'` and restores it afterwards. If an image has grey white, check this first.
- **Centre on the on-screen silhouette, not on the bounding box.** Every vertex is projected through the current view and only `view_location` moves, in the view plane, until the 2D extent is centred. Rotation and distance stay intact: what matters to the user is the inclination and zoom they chose. The maths lives in the plugin's `lib/view_projection.py`.
- **Proportions.** The viewport render uses the proportions of the render resolution, not those of the window. That is why the script sets `resolution_y = width × region_height / region_width`; otherwise the framing shifts.
- **Restoring.** After the shot the overlays come back on, because the user needs them to navigate, and the render settings go back to what they were. The centring, however, stays.
- **A series of parts** (for example grippers 02…12): one part at a time. Isolate the part with `isolate=True` or let the user show it, wait for them to adjust zoom and angle, then shoot. The user's starting view is the top view: do not adapt it to the part's shape on your own initiative.
- **Camera view**: the script stops, because centring would move the camera. Ask the user to leave the camera view (Numpad 0).
