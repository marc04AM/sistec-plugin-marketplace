# Blender: PLY vertex colours

PLY imports arrive with a colour attribute but no material, and Blender's Solid
viewport defaults to material colour — so the model renders flat grey and the
colours look lost when they are not. Whenever inspecting or modifying a Blender
scene via MCP, treat colour display as part of the inspection: check it and fix
it with the `blender-ply:ply-colors` skill (plugin `blender-ply`), which holds the verified procedure.

This covers the case no hook can observe — a model imported in Blender's own UI,
or grey since a previous session. Do not improvise the fix from memory: the
viewport enum name is version-dependent and the skill resolves it at runtime.
