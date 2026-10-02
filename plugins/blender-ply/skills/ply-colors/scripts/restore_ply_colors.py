"""
Restore vertex-colour display for PLY-imported meshes in Blender.

Run inside Blender through the MCP bridge via the exec wrapper in SKILL.md. It
assigns a JSON-serialisable summary to `result`, which is what the bridge sends back.

Idempotent by design: re-running it changes nothing once the scene is already
correct, so it is safe to fire after every import or whenever a model looks grey.

It never touches geometry, never overwrites an existing material, and never
changes the viewport shading *mode* (Solid / Material Preview / Rendered) — that
is the user's own view preference, so it is only reported, never overridden.
"""

import bpy

report = {
    "viewports": [],
    "objects": [],
    "notes": [],
    "changed": False,
    "blender": bpy.app.version_string,
}


def _active_color_attribute(mesh):
    """Return the colour attribute Blender will actually draw, or None."""
    if not mesh.color_attributes:
        return None
    return mesh.color_attributes.active_color or mesh.color_attributes[0]


# ---------------------------------------------------------------------------
# 1. Solid shading: draw the colour attribute instead of the (usually absent)
#    material. The enum member differs between Blender versions -- 'VERTEX' on
#    5.x, 'ATTRIBUTE' on some builds -- so resolve it instead of hard-coding.

enum_ids = [
    i.identifier
    for i in bpy.types.View3DShading.bl_rna.properties["color_type"].enum_items
]
target = next((n for n in ("VERTEX", "ATTRIBUTE") if n in enum_ids), None)
report["color_type_enum"] = enum_ids
report["color_type_target"] = target

if target is None:
    report["notes"].append(
        "No vertex/attribute member in View3DShading.color_type ({}). "
        "Solid shading cannot show vertex colours on this build.".format(enum_ids)
    )
else:
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != "VIEW_3D":
                continue
            for space in area.spaces:
                if space.type != "VIEW_3D":
                    continue
                shading = space.shading
                entry = {
                    "screen": window.screen.name,
                    "shading_type": shading.type,
                    "color_type_before": shading.color_type,
                }
                if shading.color_type != target:
                    shading.color_type = target
                    report["changed"] = True
                entry["color_type_after"] = shading.color_type
                area.tag_redraw()
                if shading.type == "WIREFRAME":
                    report["notes"].append(
                        "A viewport is in Wireframe: no surface colour is drawn "
                        "there regardless of this setting."
                    )
                report["viewports"].append(entry)

# ---------------------------------------------------------------------------
# 2. Material Preview / Rendered ignore the Solid colour setting entirely: they
#    need a real material that routes the colour attribute into Base Color.
#    Only meshes that carry colours and have no material get one, so nothing the
#    user (or an earlier import) set up is ever clobbered.

for ob in bpy.data.objects:
    if ob.type != "MESH":
        continue
    mesh = ob.data
    attr = _active_color_attribute(mesh)
    if attr is None:
        continue

    info = {
        "object": ob.name,
        "color_attribute": attr.name,
        "domain": attr.domain,
        "data_type": attr.data_type,
        "action": None,
    }

    existing = [s.material for s in ob.material_slots if s.material]
    if existing:
        # Respect what is already there, but say whether it can actually show
        # the colours -- a plain grey material is the usual reason a model still
        # looks flat in Material Preview.
        wired = any(
            node.bl_idname in ("ShaderNodeVertexColor", "ShaderNodeAttribute")
            for mat in existing
            if mat.use_nodes and mat.node_tree
            for node in mat.node_tree.nodes
        )
        info["action"] = "kept-existing-material"
        info["existing_materials"] = [m.name for m in existing]
        info["reads_color_attribute"] = wired
        if not wired:
            report["notes"].append(
                "{!r} already has material(s) {} that do not read a colour "
                "attribute, so Material Preview/Rendered will not show the PLY "
                "colours. Left untouched -- ask before changing it.".format(
                    ob.name, [m.name for m in existing]
                )
            )
        report["objects"].append(info)
        continue

    # Name the material after the object so it stays findable and matches the
    # naming already in the file.
    mat_name = "{:s}_{:s}".format(ob.name, attr.name)
    mat = bpy.data.materials.get(mat_name)
    created = mat is None
    if created:
        mat = bpy.data.materials.new(mat_name)

    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    out_node = tree.nodes.new("ShaderNodeOutputMaterial")
    out_node.location = (300, 0)
    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)

    if hasattr(bpy.types, "ShaderNodeVertexColor"):
        src = tree.nodes.new("ShaderNodeVertexColor")
        src.layer_name = attr.name
    else:
        src = tree.nodes.new("ShaderNodeAttribute")
        src.attribute_name = attr.name
    src.location = (-300, 0)

    tree.links.new(src.outputs["Color"], bsdf.inputs["Base Color"])
    tree.links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = 0.5
    bsdf.inputs["Metallic"].default_value = 0.0

    mesh.materials.append(mat)
    report["changed"] = True
    info["action"] = "created-material" if created else "reused-material"
    info["material"] = mat.name
    info["node"] = src.bl_idname
    report["objects"].append(info)

if not report["objects"]:
    report["notes"].append(
        "No mesh carries a colour attribute: these PLY files have no vertex "
        "colours to show. Do not invent materials to compensate."
    )

result = report
