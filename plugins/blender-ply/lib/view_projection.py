"""
Shared viewport maths for the blender-ply skill scripts (center-blender, snapshot-ply,
view-ply). Runs inside Blender; each script loads it by path, starting from the
__file__ that the SKILL.md exec wrapper passes in.

The centring method: project every vertex through the live view and move only
view_location (in the view plane) until the model's *screen* extent is centred.
The bounding-box centre is not enough for shapes that do not fill their box evenly,
and in perspective the near part of the model looks bigger than the far part.
view_rotation (the inclination) is never changed.
"""

import bpy
import numpy as np
from mathutils import Matrix, Vector


def world_verts(obs):
    """Evaluated world-space vertex coordinates of `obs`, as an (N, 3) array."""
    dg = bpy.context.evaluated_depsgraph_get()
    chunks = []
    for o in obs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        n = len(me.vertices)
        if n:
            co = np.empty(n * 3, dtype=np.float64)
            me.vertices.foreach_get("co", co)
            M = np.array(o.matrix_world, dtype=np.float64)
            chunks.append(co.reshape(n, 3) @ M[:3, :3].T + M[:3, 3])
        ev.to_mesh_clear()
    return np.concatenate(chunks) if chunks else np.zeros((0, 3))


def view_matrix(rot, loc, dist):
    return (Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
            @ Matrix.Translation((0, 0, dist))).inverted()


def to_view(V, rot, loc, dist):
    """World-space vertices -> view space (camera looks down -Z)."""
    M = np.array(view_matrix(rot, loc, dist), dtype=np.float64)
    return V @ M[:3, :3].T + M[:3, 3]


def proj_scale(space, region, persp, dist):
    """(sx, sy) with x_ndc = sx * x_view (/ -z_view in perspective).

    Computed, not read from region_3d.window_matrix: that matrix is refreshed only on
    redraw, so right after a perspective/ortho switch it is stale and the centring
    diverges. The viewport behaves as a 72 mm sensor fitted on the longer side
    (measured on Blender 5.2: persp P00 = lens/36, ortho P00 = lens/(36*dist))."""
    w, h = max(region.width, 1), max(region.height, 1)
    s = space.lens / 36.0
    if not persp:
        s /= max(dist, 1e-9)
    return (s, s * w / h) if w >= h else (s * h / w, s)


def extent(Vm, sx, sy, persp):
    """Screen extent (xmin, xmax, ymin, ymax) in NDC, or None if a vertex is behind the eye."""
    if persp:
        d = -Vm[:, 2]
        if np.any(d <= 1e-9):
            return None
        x, y = sx * Vm[:, 0] / d, sy * Vm[:, 1] / d
    else:
        x, y = sx * Vm[:, 0], sy * Vm[:, 1]
    return float(x.min()), float(x.max()), float(y.min()), float(y.max())


def centre(V, space, region, rot, loc, dist, persp, fit=False, fill=0.9,
           grow_if_behind=False, iterations=25):
    """Pan (and optionally zoom) until the screen extent of V is centred.

    fit: False never touches the zoom, True always zooms so the model fills `fill`,
    "auto" zooms out only when the model does not fit. When part of V is behind the
    eye, grow_if_behind=True backs the view off and retries; otherwise it stops.
    Returns (loc, dist, ext): ext is the last extent measured, None if V was behind."""
    rot3 = rot.to_matrix()
    zoom = fit is True
    ext = None
    for _ in range(iterations):
        Vm = to_view(V, rot, loc, dist)
        sx, sy = proj_scale(space, region, persp, dist)
        ext = extent(Vm, sx, sy, persp)
        if ext is None:
            if not grow_if_behind:
                break
            dist *= 1.5
            continue
        cx, cy = (ext[0] + ext[1]) / 2, (ext[2] + ext[3]) / 2
        span = max(ext[1] - ext[0], ext[3] - ext[2]) / 2        # 1.0 = touches the frame
        if fit == "auto" and span > 0.97:
            zoom = True
        if persp:
            depth = max(float(-Vm[:, 2].mean()), 1e-6)
            dx, dy = cx * depth / sx, cy * depth / sy
        else:
            dx, dy = cx / sx, cy / sy
        loc = loc + rot3 @ Vector((dx, dy, 0.0))
        done = abs(cx) < 1e-4 and abs(cy) < 1e-4
        if zoom and span > 1e-9 and abs(span - fill) > 1e-3:
            if persp:
                dist += depth * span / fill - depth
            else:
                dist *= span / fill
            done = False
        if done:
            break
    return loc, dist, ext


def frame_fill(ext):
    """Half the larger NDC span: 1.0 means the model touches the frame."""
    return max(ext[1] - ext[0], ext[3] - ext[2]) / 2
