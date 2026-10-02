"""
SnapshotPLY -- centre the model on screen keeping the user's inclination, then save a
clean image (white background, no grid / overlays / gizmos) of the 3D viewport.

Run inside Blender through the MCP bridge via the exec wrapper in SKILL.md.
Centring and rendering happen in this ONE call on purpose: the user navigates between
tool calls, so a render fired later would catch a different view.

Centring method: project every vertex through the live view and move only
view_location (in the view plane) until the model's *screen* extent is centred.
The bounding-box centre is not enough for shapes that do not fill their box evenly.
view_rotation (the inclination) and, unless fit=True, view_distance (the zoom) are
never touched.

The image is an OpenGL viewport render (render.opengl, view_context=True): no camera
and no lights needed, vertex colours come out exactly as seen in Solid mode.

PARAMS (all optional):
  target        object name; default = active/selected meshes, else all visible meshes
  output        full .png path; default = <folder of the .blend>/<object>_viewport.png
  width         image width in px, default 2400 (height follows the viewport aspect)
  fit           default False; True also adjusts the zoom so the model fills `fill`
  fill          default 0.9 (fraction of the frame used when fit=True)
  isolate       default False; True hides the other objects for the shot only
  restore       default True; put overlays/background/render settings back afterwards
  overwrite     default False; if the file exists a _2, _3 ... suffix is added
"""

import importlib.util
import os

import bpy

PARAMS = globals().get("PARAMS") or {}
report = {"notes": [], "changed": []}

# Shared viewport maths: <plugin>/lib/view_projection.py, found from this file's path.
_lib = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))), "lib", "view_projection.py")
_spec = importlib.util.spec_from_file_location("blender_ply_view", _lib)
vp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vp)


def pick_view():
    """The largest 3D viewport of the active window, with its WINDOW region."""
    best = None
    win = bpy.context.window or bpy.context.window_manager.windows[0]
    for area in win.screen.areas:
        if area.type != "VIEW_3D":
            continue
        region = next((r for r in area.regions if r.type == "WINDOW"), None)
        if region and (best is None or region.width * region.height > best[2].width * best[2].height):
            best = (win, area, region)
    return best


view = pick_view()
if view is None:
    result = {"error": "No 3D view open."}
else:
    win, area, region = view
    space = area.spaces.active
    r3d = space.region_3d
    scene = bpy.context.scene

    # ------------------------------------------------------------ target
    name = PARAMS.get("target")
    if name:
        targets = [bpy.data.objects[name]] if name in bpy.data.objects else []
    else:
        sel = [o for o in bpy.context.selected_objects if o.type == "MESH"]
        act = bpy.context.view_layer.objects.active
        targets = sel or ([act] if act and act.type == "MESH" else [])
        targets = [o for o in targets if o.visible_get()] or \
                  [o for o in scene.objects if o.type == "MESH" and o.visible_get()]
    report["targets"] = [o.name for o in targets]

    if not targets:
        result = {"error": "No visible model to photograph."}
    elif r3d.view_perspective == "CAMERA":
        result = {"error": "The view is through the camera: leave the camera view (Numpad 0) "
                           "and re-run, otherwise centring would move the camera."}
    else:
        V = vp.world_verts(targets)
        persp = r3d.view_perspective == "PERSP"
        fill = PARAMS.get("fill", 0.9)
        fit = PARAMS.get("fit", False)

        # ------------------------------------------------------------ centre (+ fit)
        loc, dist, ext = vp.centre(V, space, region, r3d.view_rotation.copy(),
                                   r3d.view_location.copy(), r3d.view_distance, persp,
                                   fit=fit, fill=fill)
        r3d.view_location = loc
        r3d.view_distance = dist
        if ext is None:
            report["notes"].append("Part of the model is behind the viewpoint: "
                                   "zoom out (or use fit=True) and re-run.")
        else:
            span = vp.frame_fill(ext)
            report["frame_fill"] = round(span, 3)
            if span > 1.0 and not fit:
                report["notes"].append(
                    "The model goes out of frame (fill {:.2f}): re-run with "
                    "fit=True or zoom out.".format(span))
        report["view"] = {"location": [round(v, 3) for v in loc], "distance": round(dist, 3),
                          "perspective": r3d.view_perspective}

        # ------------------------------------------------------------ output path
        out = PARAMS.get("output")
        if not out and bpy.data.filepath:
            folder = os.path.dirname(bpy.data.filepath)
            base = targets[0].name if len(targets) == 1 else \
                os.path.splitext(os.path.basename(bpy.data.filepath))[0]
            safe = "".join(ch if ch not in '<>:"/\\|?*' else "_" for ch in base)
            out = os.path.join(folder, safe + "_viewport.png")
        if out and not PARAMS.get("overwrite", False) and os.path.exists(out):
            stem, ext_ = os.path.splitext(out)
            k = 2
            while os.path.exists("{}_{}{}".format(stem, k, ext_)):
                k += 1
            out = "{}_{}{}".format(stem, k, ext_)

        if out:
            # -------------------------------------------------------- clean look
            sh, ov, rd = space.shading, space.overlay, scene.render
            saved = {
                "show_overlays": ov.show_overlays, "show_gizmo": space.show_gizmo,
                "background_type": sh.background_type,
                "background_color": tuple(sh.background_color),
                "view_transform": scene.view_settings.view_transform,
                "look": scene.view_settings.look,
                "res": (rd.resolution_x, rd.resolution_y, rd.resolution_percentage),
                "filepath": rd.filepath, "format": rd.image_settings.file_format,
                "color_mode": rd.image_settings.color_mode,
                "film_transparent": rd.film_transparent,
            }
            hidden = []
            if PARAMS.get("isolate", False):
                for o in scene.objects:
                    if o not in targets and o.visible_get():
                        o.hide_set(True)
                        hidden.append(o)
            try:
                ov.show_overlays = False       # grid, axes, outline, 3D cursor, texts
                space.show_gizmo = False       # navigation gizmo
                sh.background_type = "VIEWPORT"
                sh.background_color = (1.0, 1.0, 1.0)
                try:
                    # AgX tone-maps pure white down to ~#c8c8c8 in the saved file.
                    scene.view_settings.view_transform = "Standard"
                    scene.view_settings.look = "None"
                except Exception as e:  # enum lists can be unreliable; set and catch
                    report["notes"].append("view_transform: {}".format(e))
                width = int(PARAMS.get("width", 2400))
                rd.resolution_x = width
                rd.resolution_y = max(1, round(width * region.height / region.width))
                rd.resolution_percentage = 100
                rd.film_transparent = False
                rd.image_settings.file_format = "PNG"
                rd.image_settings.color_mode = "RGB"
                rd.filepath = out
                with bpy.context.temp_override(window=win, area=area, region=region):
                    bpy.ops.render.opengl(write_still=True, view_context=True)
                report["image"] = out
                report["size_px"] = [rd.resolution_x, rd.resolution_y]
                report["exists"] = os.path.exists(out)
            finally:
                if PARAMS.get("restore", True):
                    ov.show_overlays = saved["show_overlays"]
                    space.show_gizmo = saved["show_gizmo"]
                    sh.background_type = saved["background_type"]
                    sh.background_color = saved["background_color"]
                    try:
                        scene.view_settings.view_transform = saved["view_transform"]
                        scene.view_settings.look = saved["look"]
                    except Exception:
                        pass
                    rd.resolution_x, rd.resolution_y, rd.resolution_percentage = saved["res"]
                    rd.filepath = saved["filepath"]
                    rd.image_settings.file_format = saved["format"]
                    rd.image_settings.color_mode = saved["color_mode"]
                    rd.film_transparent = saved["film_transparent"]
                for o in hidden:
                    o.hide_set(False)
                area.tag_redraw()
            result = report
        else:
            report["error"] = ("The .blend file is not saved: pass PARAMS['output'] "
                               "(full path of the .png). The view is already centred.")
            result = report
