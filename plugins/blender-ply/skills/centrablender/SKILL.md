---
name: centrablender
description: >-
  CentraBlender — in Blender, puts the visible 3D model in the middle of the screen by moving only
  the view, without changing the inclination and keeping the zoom (it zooms out only if the model
  does not fit). It does not touch geometry, objects, origins or selection. Use it when the user
  invokes /blender-ply:centrablender or CentraBlender, and whenever they ask to centre the model on
  screen in Blender — "centra il modello sullo schermo", "mettilo al centro della vista", "il
  modello è spostato di lato / fuori schermo / non si vede tutto", "centra la vista sul pezzo
  senza ruotarla", "riportami il modello al centro", "centre the model", "the model is off screen"
  — even if the skill is not named. Not for moving the origin (CentraPLY), for the first setup
  after an import (VisualizzaPLY) or for saving an image (FotografaPLY).
---

# CentraBlender

Goal: the visible model must sit **in the middle of the screen**, as the user is looking at it. The inclination the user chose stays theirs, and so does the zoom, unless the model does not fit on screen.

This changes the **view** only: no object moves, and origin, 3D cursor, selection, mode, colours and shading settings stay the same. That is why the skill does not ask for confirmation.

## Procedure

1. **Run the script** with `mcp__Blender__execute_blender_code`:
   ```python
   PARAMS = {}
   p = r"${CLAUDE_SKILL_DIR}/scripts/centra_blender.py"
   g = {"PARAMS": PARAMS, "__file__": p}
   exec(compile(open(p, encoding="utf-8").read(), p, "exec"), g)
   result = g["result"]
   ```
   Parameters, if needed:
   - `target`: a name or a list of names. By default every visible mesh is used, i.e. "the model visible on screen".
   - `fit`:
     - `"auto"` (default): the zoom backs off only if the model does not fit;
     - `True`: always adjusts the zoom so the model fills about 90% of the frame. Use it if the user also asks to "enlarge it" or "fill the screen";
     - `False`: the zoom is never touched.
   - `fill`: default 0.9.
   - `all_views`: default True, centres in every open 3D view.

   If the user has selected a part and says "centre *this*", pass the names of the selected objects in `target`. If instead they want to centre a group of vertices in Edit Mode, the native command is View → Frame Selected (numpad `.`, which is `,` on the Italian keyboard). That command, however, changes zoom and pivot.

2. **Read the report.** For each view:
   - `centre_ndc`: centre of the model on screen, should be about [0, 0];
   - `frame_fill`: how much of the frame the model takes up (1.0 = touches the edge);
   - `zoom_changed`: whether the zoom was backed off;
   - `clip_changed`: whether the clip range was widened because it was cutting the model;
   - `skipped`: for example the camera view.

   Relay `notes` and `error` to the user.

3. **Check with a screenshot**: `mcp__Blender__get_screenshot_of_window_as_image` with `size_limit_in_bytes: 400000`. Check that the model is whole and centred. If the screenshot is black, the Blender window is minimised: ask the user to restore it.

4. **Answer in a line or two**, in the user's language. For example: "Model centred; inclination and zoom unchanged." Or: "Centred; it did not fit on screen, so I backed the zoom off a little." The user prefers short answers.

## Why it works this way

- **Centre on the on-screen silhouette, not on the bounding box.** The bounding-box centre is fine only for shapes that fill their box. For a gripper, a frame or any irregular part, and in perspective where the near part looks bigger, the model ends up off-centre. The script projects every vertex through the current view and moves `view_location` in the view plane until the 2D extent is centred.
- **View Selected / View All are not used.** Those commands change the zoom, and with Smooth View they animate the view, so values read right afterwards are stale. They also change the rotation pivot in ways the user did not ask for.
- **The projection is computed, not read.** `region_3d.window_matrix` is refreshed only on redraw. Right after a perspective/orthographic switch it is stale, and the centring diverged (positions of 10²²). The script instead uses the formula measured on Blender 5.2: a virtual 72 mm sensor on the long side, i.e. P00 = lens/36 in perspective and P00 = lens/(36·dist) in orthographic. The maths lives in the plugin's `lib/view_projection.py`.
- **The clip range.** CAD models are in mm and the default `clip_end` is 1000. After the move the script checks that the model is not cut and, if needed, widens the clip range. It does not widen it more than necessary, because a huge far/near ratio produces z-fighting streaks.
- **Camera view.** There the view can move only by moving the camera, which is a scene object. The script stops and says so.
- **Viewpoint inside the model.** If part of the model is behind the viewer, for example after a very close zoom, panning sideways is not enough. The script first backs off and then centres.
- **The scene changes between turns**, because the user navigates. Re-run the script instead of reusing old values.
