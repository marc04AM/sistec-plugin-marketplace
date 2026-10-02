"""
CentraPLY -- make the selected vertex (or the midpoint of the selected vertices) the
common origin: object origin = 3D cursor = world origin (0,0,0).

Run inside Blender through the MCP bridge via the exec wrapper in SKILL.md.

How: the mesh data is translated by -P (P = chosen point, in object space) and the
object location is set to 0. The model's orientation and scale are left as they are,
so only a translation happens: the chosen point lands on the world origin, the object
origin sits on it, and the 3D cursor is put there too. The viewport follows by the
same amount, so the model stays where it was on screen.

Why the mesh and not only the object: PLY export ignores the object transform, so an
origin that lives only in `location` is lost in the exported file.

Selection is read from the live edit-bmesh when the object is in Edit Mode (the mesh
data is stale there) and the translation is applied to that bmesh directly -- leaving
Edit Mode would flush and can silently merge duplicate vertices.

CAD PLY files duplicate vertices at shared corners, so one "vertex" the user clicks is
often 2-3 coincident copies: the points are de-duplicated by position before the
midpoint is taken, otherwise the copies would bias it.

PARAMS (all optional):
  mode      "mean" (default: centroid of the distinct selected points) or
            "bbox" (centre of the selection's bounding box)
  dry_run   default False; True only reports the point, changes nothing
  follow_view default True; shift the viewport by the same amount
  tol       default 1e-4 (merge distance for coincident points)
"""

import bpy
import bmesh
import math
from mathutils import Matrix, Vector

PARAMS = globals().get("PARAMS") or {}
MODE = PARAMS.get("mode", "mean")
TOL = PARAMS.get("tol", 1e-4)
report = {"notes": []}


def selected_local_points(ob):
    """Selected vertex coordinates (object space) and where they came from."""
    me = ob.data
    if ob.mode == "EDIT":
        bm = bmesh.from_edit_mesh(me)
        return [v.co.copy() for v in bm.verts if v.select], "edit-bmesh"
    return [v.co.copy() for v in me.vertices if v.select], "mesh (Object Mode: last saved selection)"


def dedupe(points, tol):
    seen, out = set(), []
    q = 1.0 / tol
    for p in points:
        k = (round(p.x * q), round(p.y * q), round(p.z * q))
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out


# ---------------------------------------------------------------- find the selection
cands = [o for o in bpy.context.objects_in_mode if o.type == "MESH"] if bpy.context.mode == "EDIT_MESH" else []
if not cands:
    act = bpy.context.view_layer.objects.active
    cands = [act] if act and act.type == "MESH" else []

found = []
for o in cands:
    pts, src = selected_local_points(o)
    if pts:
        found.append((o, pts, src))

if not found:
    result = {"error": "No vertex selected. In Blender: Tab (Edit Mode), 1 (vertex select), "
                       "click the vertex (Shift+click to add more), then re-run."}
elif len(found) > 1:
    result = {"error": "Vertices selected on more than one object ({}): select them on a single "
                       "model.".format([o.name for o, _, _ in found])}
else:
    ob, raw, src = found[0]
    pts = dedupe(raw, TOL)
    Mw = ob.matrix_world.copy()
    if MODE == "bbox":
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        P_loc = (lo + hi) / 2
    else:
        P_loc = sum(pts, Vector()) / len(pts)
    P_world = Mw @ P_loc

    report.update({
        "object": ob.name, "mode_blender": ob.mode, "source": src,
        "selected_vertices": len(raw), "distinct_points": len(pts), "method": MODE,
        "point_world_before": [round(v, 4) for v in P_world],
        "point_local": [round(v, 4) for v in P_loc],
    })
    if len(pts) > 2:
        d = [(Mw @ p - P_world).length for p in pts]
        report["distance_from_point"] = {"min": round(min(d), 4), "max": round(max(d), 4)}
        report["equidistant"] = (max(d) - min(d)) <= max(1e-3, 1e-3 * max(d))
        if not report["equidistant"] and MODE == "mean":
            report["notes"].append(
                "The points are not equidistant from the midpoint: it is the centroid, not the "
                "centre of a hole/circle. If the bounding-box centre was needed, use mode='bbox'.")
    if len(pts) != len(raw):
        report["notes"].append("{} vertices selected but {} distinct points: coincident duplicates "
                               "(typical of CAD PLYs) were counted once."
                               .format(len(raw), len(pts)))
    if ob.data.users > 1:
        report["notes"].append("The mesh is shared by {} objects: they all move."
                               .format(ob.data.users))
    # From matrix_basis, so quaternion / axis-angle rotation modes are caught too.
    rot = [round(math.degrees(a), 3) for a in ob.matrix_basis.to_euler()]
    if any(abs(a) > 1e-6 for a in rot) or any(abs(s - 1) > 1e-9 for s in ob.scale):
        report["notes"].append(
            "The object has rotation {} and scale {}: they were kept (translation only). "
            "PLY export ignores them: if the file must come out oriented this way, apply "
            "them (Ctrl+A > Rotation & Scale).".format(rot, [round(s, 4) for s in ob.scale]))
    if ob.parent:
        report["notes"].append("The object has a parent ({}): location 0 is relative to the "
                               "parent.".format(ob.parent.name))

    if PARAMS.get("dry_run", False):
        report["dry_run"] = True
        result = report
    else:
        loc_before = [round(v, 4) for v in ob.location]
        T = Matrix.Translation(-P_loc)
        if ob.mode == "EDIT":
            bm = bmesh.from_edit_mesh(ob.data)
            bmesh.ops.translate(bm, verts=bm.verts[:], vec=-P_loc)
            bmesh.update_edit_mesh(ob.data)
        else:
            ob.data.transform(T)
            ob.data.update()
        # The origin now coincides with the point; zero the world translation (keeping
        # rotation and scale) so origin and point sit on the world origin. Written on
        # matrix_world so it also holds when the object has a parent.
        ob.matrix_world = Matrix.Translation(-Mw.translation) @ Mw
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

        # Every point of the model moved by D = -P_world: shift the views by the same
        # amount so the model stays where it was on screen.
        D = -P_world
        if PARAMS.get("follow_view", True):
            for win in bpy.context.window_manager.windows:
                for area in win.screen.areas:
                    if area.type == "VIEW_3D":
                        r3d = area.spaces.active.region_3d
                        if r3d and r3d.view_perspective != "CAMERA":
                            r3d.view_location = r3d.view_location + D
                        area.tag_redraw()

        # Verify: the chosen point is now at the world origin.
        if ob.mode == "EDIT":
            bm = bmesh.from_edit_mesh(ob.data)
            now = [ob.matrix_world @ v.co for v in bm.verts if v.select]
        else:
            now = [ob.matrix_world @ v.co for v in ob.data.vertices if v.select]
        now = dedupe(now, TOL)
        if MODE == "bbox":
            lo = Vector((min(p.x for p in now), min(p.y for p in now), min(p.z for p in now)))
            hi = Vector((max(p.x for p in now), max(p.y for p in now), max(p.z for p in now)))
            chk = (lo + hi) / 2
        else:
            chk = sum(now, Vector()) / len(now)
        try:
            bpy.ops.ed.undo_push(message="CentraPLY")
        except Exception as e:
            report["notes"].append("undo_push: {}".format(e))

        report.update({
            "location_before": loc_before,
            "location_after": [round(v, 4) for v in ob.location],
            "world_shift": [round(v, 4) for v in D],
            "point_world_after": [round(v, 6) for v in chk],
            "ok": chk.length < 1e-3,
            "cursor": [0.0, 0.0, 0.0],
            "undo": "Ctrl+Z undoes it (step 'CentraPLY')",
        })
        result = report
