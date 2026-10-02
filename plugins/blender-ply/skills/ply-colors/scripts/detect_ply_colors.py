"""
READ-ONLY detection: is Blender currently failing to show vertex colours?

Mutates nothing. Run it through `mcp__Blender__execute_blender_code` via the exec
wrapper in SKILL.md, or over the raw bridge socket
(`{"type":"execute","code":<this>,"strict_json":true}` + b"\\x00" to
127.0.0.1:9876). Assigns a JSON summary to `result`.

`needs_fix` is deliberately narrow: it is true only when the user could
actually see the problem right now, given the shading mode each viewport is
in. Nudging about a material that Material Preview would need while the user
is working happily in Solid mode is noise, and a warning that cries wolf is a
warning that gets skipped.
"""

import bpy

COLOUR_NODES = ("ShaderNodeVertexColor", "ShaderNodeAttribute")


def _active_colour_attribute(mesh):
    if not mesh.color_attributes:
        return None
    return mesh.color_attributes.active_color or mesh.color_attributes[0]


def _reads_colour_attribute(material):
    if not material.use_nodes or not material.node_tree:
        return False
    return any(n.bl_idname in COLOUR_NODES for n in material.node_tree.nodes)


enum_ids = [
    i.identifier
    for i in bpy.types.View3DShading.bl_rna.properties["color_type"].enum_items
]
target = next((n for n in ("VERTEX", "ATTRIBUTE") if n in enum_ids), None)

# --- meshes carrying colours, and whether they could show them in a shader
coloured, unmaterialed, greyed = [], [], []
for ob in bpy.data.objects:
    if ob.type != "MESH":
        continue
    attr = _active_colour_attribute(ob.data)
    if attr is None:
        continue
    coloured.append(ob.name)
    mats = [s.material for s in ob.material_slots if s.material]
    if not mats:
        unmaterialed.append(ob.name)
    elif not any(_reads_colour_attribute(m) for m in mats):
        greyed.append({"object": ob.name, "materials": [m.name for m in mats]})

# --- viewports, and which of them is currently mis-showing colour
solid_wrong, preview_wrong, viewports = [], [], []
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type != "VIEW_3D":
            continue
        for space in area.spaces:
            if space.type != "VIEW_3D":
                continue
            shading = space.shading
            viewports.append({
                "screen": window.screen.name,
                "shading_type": shading.type,
                "color_type": shading.color_type,
            })
            if shading.type == "SOLID" and target and shading.color_type != target:
                solid_wrong.append(window.screen.name)
            elif shading.type in ("MATERIAL", "RENDERED") and (unmaterialed or greyed):
                preview_wrong.append(window.screen.name)

result = {
    "coloured_meshes": coloured,
    "meshes_without_material": unmaterialed,
    "meshes_with_non_colour_material": greyed,
    "viewports": viewports,
    "color_type_target": target,
    "solid_viewports_wrong": solid_wrong,
    "shader_viewports_wrong": preview_wrong,
    # Only true when the problem is visible in the mode the user is actually in.
    "needs_fix": bool(coloured) and bool(solid_wrong or preview_wrong),
    "blender": bpy.app.version_string,
}
