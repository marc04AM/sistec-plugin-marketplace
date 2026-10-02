"""
CenterBlender -- put the visible 3D model in the middle of the screen in Blender.

Run inside Blender through the MCP bridge via the exec wrapper in SKILL.md.
Assigns a JSON-serialisable dict to `result`.

Only the viewport moves: no geometry, object, selection or mode is touched.
Method: project every visible vertex through the live view and shift only
view_location (in the view plane) until the model's *screen* extent is centred.
The bounding-box centre is not enough for shapes that do not fill their box evenly,
and in perspective the near part of the model looks bigger than the far part.
The inclination (view_rotation) is never changed. The zoom (view_distance) is kept,
except when the model does not fit on screen: then it is zoomed out just enough
(fit="auto"). The clip range is widened if the model would be cut by it.

PARAMS (all optional):
  target   object name, or list of names; default = every visible mesh in the view
  fit      "auto" (default: zoom out only if the model does not fit),
           True (always zoom so the model fills `fill`), False (never touch the zoom)
  fill     default 0.9 (fraction of the frame used when zooming)
  all_views default True (centre in every 3D viewport; False = only the largest)
"""

import importlib.util
import os

import bpy
import numpy as np
from mathutils import Vector

PARAMS = globals().get("PARAMS") or {}
FIT = PARAMS.get("fit", "auto")
FILL = float(PARAMS.get("fill", 0.9))
report = {"notes": [], "views": []}

# Shared viewport maths: <plugin>/lib/view_projection.py, found from this file's path.
_lib = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))), "lib", "view_projection.py")
_spec = importlib.util.spec_from_file_location("blender_ply_view", _lib)
vp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vp)


def centre_view(area, V):
    space = area.spaces.active
    r3d = space.region_3d
    region = next((r for r in area.regions if r.type == "WINDOW"), None)
    info = {"area": area.as_pointer() % 10000}
    if region is None or r3d is None:
        info["skipped"] = "no 3D region"
        return info
    if r3d.view_perspective == "CAMERA":
        info["skipped"] = ("camera view: centring would move the camera. Leave it with "
                           "Numpad 0 and re-run.")
        return info

    persp = r3d.view_perspective == "PERSP"
    rot = r3d.view_rotation.copy()
    loc = r3d.view_location.copy()
    dist = r3d.view_distance
    dist0 = dist
    fit = FIT

    # A viewpoint inside or behind the model cannot be centred by panning: back off first.
    if persp and np.any(-vp.to_view(V, rot, loc, dist)[:, 2] <= 1e-6):
        radius = float(np.linalg.norm(V.max(0) - V.min(0))) / 2
        loc = Vector(V.mean(0))
        dist = radius * 3.0
        fit = FIT is not False
        info["backed_off"] = True

    loc, dist, ext = vp.centre(V, space, region, rot, loc, dist, persp, fit=fit, fill=FILL,
                               grow_if_behind=True)
    r3d.view_location = loc
    r3d.view_distance = dist

    # Make sure the clip range does not cut the model at the new position.
    depth = -vp.to_view(V, rot, loc, dist)[:, 2]
    far, near = float(depth.max()), float(depth.min())
    clip_changed = []
    if persp and far > space.clip_end * 0.98:
        space.clip_end = far * 1.5
        clip_changed.append("clip_end -> {:.1f}".format(space.clip_end))
    if persp and 0 < near < space.clip_start * 1.02:
        space.clip_start = max(near * 0.5, 1e-3)
        clip_changed.append("clip_start -> {:.4f}".format(space.clip_start))
    area.tag_redraw()

    if ext:
        info["frame_fill"] = round(vp.frame_fill(ext), 3)
        info["centre_ndc"] = [round((ext[0] + ext[1]) / 2, 5), round((ext[2] + ext[3]) / 2, 5)]
    info.update({
        "perspective": r3d.view_perspective,
        "location": [round(v, 3) for v in loc],
        "distance_before": round(dist0, 3), "distance_after": round(dist, 3),
        "zoom_changed": abs(dist - dist0) > 1e-6,
        "rotation_unchanged": True,
    })
    if clip_changed:
        info["clip_changed"] = clip_changed
    return info


# ---------------------------------------------------------------- targets
scene = bpy.context.scene
t = PARAMS.get("target")
if t:
    names = [t] if isinstance(t, str) else list(t)
    targets = [bpy.data.objects[n] for n in names if n in bpy.data.objects]
    missing = [n for n in names if n not in bpy.data.objects]
    if missing:
        report["notes"].append("Objects not found: {}".format(missing))
else:
    targets = [o for o in scene.objects if o.type == "MESH" and o.visible_get()]
report["targets"] = [o.name for o in targets]

if not targets:
    result = {"error": "No visible 3D model in the scene to centre."}
else:
    V = vp.world_verts(targets)
    if len(V) == 0:
        result = {"error": "The visible models have no vertices.", **report}
    else:
        areas = []
        for win in bpy.context.window_manager.windows:
            for area in win.screen.areas:
                if area.type == "VIEW_3D":
                    reg = next((r for r in area.regions if r.type == "WINDOW"), None)
                    areas.append((reg.width * reg.height if reg else 0, area))
        areas.sort(key=lambda a: -a[0])
        if not PARAMS.get("all_views", True):
            areas = areas[:1]
        if not areas:
            result = {"error": "No 3D view open.", **report}
        else:
            for _, area in areas:
                report["views"].append(centre_view(area, V))
            for v in report["views"]:
                if v.get("zoom_changed") and FIT == "auto":
                    report["notes"].append("The model did not fit on screen: zoomed out just "
                                           "enough (inclination unchanged).")
                    break
            result = report
