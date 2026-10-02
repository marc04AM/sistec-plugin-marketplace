---
name: center-ply
description: >-
  CenterPLY — in Blender, brings the selected vertex (or the midpoint of the selected vertices) to
  the world origin and makes the object origin and the 3D cursor coincide there as well ("the
  three points that line up"), moving the mesh so that it also holds in the exported PLY. Use it
  when the user invokes /blender-ply:center-ply or CenterPLY, and whenever they ask to move the
  origin onto the selected vertex — "porta/sposta l'origine sul vertice selezionato", "metti
  l'origine del modello e del mondo su questo punto", "origine nel punto medio dei punti
  selezionati", "centra il modello sul vertice", "centro del foro come origine", "fai combaciare
  origine oggetto, cursore e origine mondo", "set the origin to this vertex" — even if the skill
  is not named. It does not rotate the model; orienting the axes (X on the short side, Z outward…)
  takes an extra step, described in the skill.
---

# CenterPLY

The goal, as the user has always meant it: **object origin = 3D cursor = world origin (0,0,0)**, all on the chosen point. The chosen point is the vertex selected in Blender, or the midpoint of the selected vertices.

Changing the reference, or moving only the origin with Set Origin, is not enough: the part must really sit with that point on the world zero.

## Procedure

1. **Check that there is a selection.** The user must be in Edit Mode, with one or more vertices selected. The script reads the selection from the live bmesh, because in Edit Mode the mesh data is stale. If there is no selection the script says so: explain to the user how to select (Tab → key 1 → click the vertex, Shift+click to add more) and wait for them to answer "done".

2. **Preview first, if the point is ambiguous.** With `dry_run=True` the script only reports the point, changing nothing. Use it when:
   - the selection contains many vertices;
   - the user talked about the "centre" of something, such as a hole or a face;
   - you are unsure which vertex they meant.

   The user often corrects their own directions ("it was the hole underneath"), so showing them the point first is cheap.

3. **Run the script** with `mcp__Blender__execute_blender_code`:
   ```python
   PARAMS = {}
   p = r"${CLAUDE_SKILL_DIR}/scripts/center_ply.py"
   g = {"PARAMS": PARAMS, "__file__": p}
   exec(compile(open(p, encoding="utf-8").read(), p, "exec"), g)
   result = g["result"]
   ```
   Parameters:
   - `mode`: `"mean"` (default) = centroid of the distinct points; `"bbox"` = centre of the selection's bounding box;
   - `dry_run`;
   - `follow_view`: default True, moves the view together with the model so it stays where it was on screen;
   - `tol`.

   The script:
   - translates the **mesh** by −P;
   - zeroes the object translation, keeping rotation and scale;
   - puts the cursor at (0,0,0);
   - checks that the point has landed on (0,0,0);
   - records a "CenterPLY" undo step (Ctrl+Z).

4. **Read the report.**
   - `ok` must be True.
   - `point_world_before`: the chosen point, i.e. how far the model moved.
   - `distinct_points` and `selected_vertices`: if they differ, there were coincident duplicates.
   - `equidistant`: with more than 2 points, says whether the midpoint really is the centre of a circle or hole.
   - `notes`: rotation or scale present, shared mesh, parent.

5. **Answer briefly**, in the user's language. For example: "Origin on vertex 752: the model moved by (−1819; −70.5; +2); object origin, cursor and world now coincide. Ctrl+Z to undo." Add the notes only if they change something for the user.

## Things to know

- **Why the mesh moves and not just the object.** PLY export ignores the object transform. An origin that exists only in the object location disappears in the exported file.
- **Do not leave Edit Mode.** Leaving it flushes and can merge duplicate vertices (21,724 → 21,723 on the Carro). The script works directly on the live bmesh and leaves the user where they are.
- **Duplicates in CAD PLYs.** At edges each face has its own copy of the vertex, so one click often selects 2–3 coincident vertices. The script counts them once, otherwise they would skew the midpoint.
- **Centre of a hole.** The midpoint of the ring vertices matches the centre only if they are equidistant; the script checks this. If they are not, say so, and if the bounding-box centre was what was needed, re-run with `mode="bbox"`.
- **Orientation.** CenterPLY only translates. If the user also asks for the axes (for example "X on the short side, Y on the long side, Z out of the face"), one more step is needed:
  - find the flat faces with a coplanar flood-fill (`normal·n > 0.9999`) sorted by area, without using `link_faces` on the edge, because with duplicated vertices it sees only one plane;
  - build the basis with `basis = Matrix((X, Y, Z)).transposed()`;
  - apply `me.transform(basis.inverted())` to the already centred mesh.

  One constraint to remember: at a corner you cannot have the short side on +X, the long side on +Y and the normal on +Z all at once (the right-handed frame forbids it). Tell the user instead of choosing yourself which condition to give up.
- **Offset from a point** (for example "+63 in X, +355 in Y from the face"): ask or check which face it is measured from. On the conveyor belt the 355 had to be taken from the *far* face of the plate. Then use `dry_run` to show the point.
- **A 90° rotation done by the user.** If the user says "I turned it 90° on Z", ask whether they rotated the view or the object.
- **Other objects in the scene.** Only the object containing the selection moves. If the scene has other parts that must stay aligned with this one (for example SPM on the Centratore), point it out and ask whether they should be moved by the same amount (`world_shift`).
- **Saving.** Do not save the `.blend` or export unless the user asks: they usually export it themselves.
