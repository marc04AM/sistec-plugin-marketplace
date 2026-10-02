"""
ViewPLY -- make an imported PLY model visible and readable in Blender's viewport.

Run inside Blender through the MCP bridge (mcp__Blender__execute_blender_code),
normally via the small exec wrapper shown in SKILL.md so that PARAMS can be passed.
Assigns a JSON-serialisable dict to `result` (the bridge rejects anything else).

What it does, in order:
  1. finds the model(s): meshes carrying a colour attribute (what a PLY import leaves)
  2. restores vertex-colour display by running the ply-colors skill script
  3. sets clip_start / clip_end from the model size (CAD PLYs are in mm: thousands
     of units, while Blender's default clip_end is 1000 -> model cut or invisible)
  4. frames the model in a 3/4 perspective view, computed (not view_selected, whose
     smooth-view animation leaves stale values and which ignores the clip)
  5. zoom preferences: zoom to mouse position + auto depth, so zooming goes where
     the user points instead of towards a far-away pivot

It never edits geometry, never changes object selection or mode, and only switches
the shading type when it is Wireframe (where no colour can be seen at all).

PARAMS (all optional):
  target        object name to frame; default = active/selected coloured mesh,
                otherwise all visible coloured meshes together
  elevation_deg default 62   (angle from the vertical; 90 = horizontal view)
  azimuth_deg   default 40   (rotation around Z)
  margin        default 1.08 (1.0 = model touches the frame)
  zoom_prefs    default True (set use_zoom_to_mouse + use_mouse_depth_navigate)
  colors        default True (run the ply-colors restore script)
"""

import importlib.util
import math
import os

import bpy
from mathutils import Euler, Vector

PARAMS = globals().get("PARAMS") or {}
# The exec wrapper passes __file__; the colours script lives in the sibling ply-colors
# skill and the shared viewport maths in <plugin>/lib.
SKILLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COLORS_SCRIPT = os.path.join(SKILLS_DIR, "ply-colors", "scripts", "restore_ply_colors.py")
_lib = os.path.join(os.path.dirname(SKILLS_DIR), "lib", "view_projection.py")
_spec = importlib.util.spec_from_file_location("blender_ply_view", _lib)
vp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vp)

report = {"blender": bpy.app.version_string, "notes": [], "changed": []}


def coloured(ob):
    return ob.type == "MESH" and len(ob.data.color_attributes) > 0


# ---------------------------------------------------------------- 1. find the model
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
candidates = [o for o in meshes if coloured(o)]
report["meshes"] = [o.name for o in meshes]
report["coloured_meshes"] = [o.name for o in candidates]

targets = []
name = PARAMS.get("target")
if name:
    ob = bpy.data.objects.get(name)
    if ob is None:
        report["error"] = "Object {!r} not found".format(name)
    else:
        targets = [ob]
else:
    active = bpy.context.view_layer.objects.active
    sel = [o for o in candidates if o.select_get()]
    if active in candidates and active.visible_get():
        targets = [active]
    elif sel:
        targets = sel
    else:
        targets = [o for o in candidates if o.visible_get()]
    if not targets and meshes:
        # A mesh without colours: still frame it, but say the file has no colours.
        targets = [o for o in meshes if o.visible_get()]
        if targets:
            report["notes"].append(
                "No mesh has a colour attribute: the PLY contains no vertex colours. "
                "Framing the model anyway, without inventing colours."
            )

if not targets and "error" not in report:
    report["error"] = (
        "No model in the scene: import the PLY (File > Import > Stanford PLY) "
        "and re-run."
    )

if "error" in report:
    result = report
else:
    report["targets"] = [o.name for o in targets]
    for o in targets:
        if o.mode != "OBJECT":
            # Attribute data reads as length 0 in Edit Mode; do not switch mode for the
            # user (leaving Edit Mode flushes and can merge duplicate vertices).
            report["notes"].append(
                "{!r} is in {} Mode: the colours still show, but to read or edit "
                "the attributes it must be back in Object Mode.".format(o.name, o.mode)
            )

    # ------------------------------------------------------------ 2. vertex colours
    if PARAMS.get("colors", True):
        if os.path.exists(COLORS_SCRIPT):
            g = {"__file__": COLORS_SCRIPT}
            exec(compile(open(COLORS_SCRIPT, encoding="utf-8").read(), COLORS_SCRIPT, "exec"), g)
            c = g.get("result", {})
            report["colors"] = {
                "color_type": [v.get("color_type_after") for v in c.get("viewports", [])],
                "objects": [
                    {"object": x.get("object"), "action": x.get("action"),
                     "attribute": x.get("color_attribute")}
                    for x in c.get("objects", [])
                ],
                "changed": c.get("changed"),
            }
            report["notes"] += c.get("notes", [])
        else:
            report["notes"].append("Colour script not found: " + COLORS_SCRIPT)

    # ------------------------------------------------------------ 3-4. clip + view
    pts = []
    for o in targets:
        pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (lo + hi) / 2
    size = hi - lo
    diag = max(size.length, 1e-6)
    radius = diag / 2
    report["bbox"] = {"min": [round(v, 3) for v in lo], "max": [round(v, 3) for v in hi],
                      "size": [round(v, 3) for v in size], "diag": round(diag, 3)}

    # Near/far ratio ~2e4 keeps depth precision: a far clip 100x the model caused
    # white z-fighting streaks on CorpoPressa, a near clip of 1-1.6 blocked close zoom.
    clip_start = max(diag / 2000.0, 0.01)
    clip_end = max(diag * 10.0, 100.0)

    rot = Euler((math.radians(PARAMS.get("elevation_deg", 62)), 0.0,
                 math.radians(PARAMS.get("azimuth_deg", 40))), "XYZ").to_quaternion()
    margin = PARAMS.get("margin", 1.08)

    views = []
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            region = next((r for r in area.regions if r.type == "WINDOW"), None)
            r3d = space.region_3d
            if region is None or r3d is None:
                continue
            if space.shading.type == "WIREFRAME":
                space.shading.type = "SOLID"
                report["changed"].append("shading Wireframe -> Solid")
            space.clip_start = clip_start
            space.clip_end = clip_end
            r3d.view_perspective = "PERSP"
            r3d.view_rotation = rot
            r3d.view_location = center
            # The larger projection scale belongs to the short side, the one that limits
            # the fit: tan(half-fov, short side) = 1 / max(sx, sy).
            w, h = max(region.width, 1), max(region.height, 1)
            half = math.atan(1.0 / max(vp.proj_scale(space, region, True, 1.0)))
            r3d.view_distance = radius / math.sin(half) * margin
            area.tag_redraw()
            views.append({"area": area.as_pointer() % 10000, "lens": space.lens,
                          "region": [w, h], "distance": round(r3d.view_distance, 3)})
    report["clip"] = {"start": round(clip_start, 4), "end": round(clip_end, 1)}
    report["views"] = views
    if not views:
        report["notes"].append("No 3D view open: cannot set the viewpoint.")

    # ------------------------------------------------------------ 5. zoom prefs
    if PARAMS.get("zoom_prefs", True):
        inp = bpy.context.preferences.inputs
        for attr in ("use_zoom_to_mouse", "use_mouse_depth_navigate"):
            if not getattr(inp, attr):
                setattr(inp, attr, True)
                report["changed"].append(attr + " = True")
    # Always state the final value, so "already on" is not mistaken for "not done".
    inp = bpy.context.preferences.inputs
    report["zoom_prefs"] = {"zoom_to_mouse": inp.use_zoom_to_mouse,
                            "auto_depth": inp.use_mouse_depth_navigate}

    result = report
