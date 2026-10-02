"""
PostToolUse observer: speak up only when Blender is actually showing a
colour-carrying PLY mesh as grey.

Design notes, because the obvious version of this hook is worse:

  * It does NOT nudge blindly. The first version did, and it fired on a scene
    that was already correct -- which is how a reminder trains its reader to
    skim past it. This version asks Blender (read-only) and stays silent when
    there is nothing to fix.
  * It does NOT fix anything itself. Deciding what to do about a mesh that
    already has a material the user built needs a conversation, and a hook
    cannot have one. It reports; Claude acts via the `blender-ply:ply-colors` skill.
  * The socket round-trip happens ONLY on the two trigger occasions (a PLY
    import, or the first Blender call of a session), never on every Blender
    tool call, so the common path costs one regex and exits.

Bridge protocol: newline-free JSON + NUL to 127.0.0.1:9876, response read
until NUL.
"""

import json
import os
import re
import socket
import sys
import tempfile
import time

BRIDGE = ("127.0.0.1", 9876)
BRIDGE_TIMEOUT = 2.0          # bounded: Blender services clients from a timer
MARKER_DIR = os.path.join(tempfile.gettempdir(), "claude-blender-ply-colors")
MARKER_MAX_AGE = 7 * 24 * 3600
SKILL = "blender-ply:ply-colors"

DETECT_SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "skills", "ply-colors", "scripts", "detect_ply_colors.py",
)

# Operator names for import; the looser third alternative catches hand-rolled
# importers. Export is deliberately absent -- writing a .ply out says nothing
# about how the viewport is displaying it.
IMPORT_RE = re.compile(
    r"ply_import|import_mesh\.ply|import[^\n]{0,80}\.ply",
    re.IGNORECASE,
)


def _prune_markers():
    """Session markers are disposable; do not let them pile up forever."""
    try:
        cutoff = time.time() - MARKER_MAX_AGE
        for name in os.listdir(MARKER_DIR):
            path = os.path.join(MARKER_DIR, name)
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
    except OSError:
        pass


def _first_touch(session_id):
    """True the first time this session reaches a Blender tool."""
    if not session_id:
        return True
    marker = os.path.join(MARKER_DIR, re.sub(r"[^A-Za-z0-9_-]", "_", session_id))
    if os.path.exists(marker):
        return False
    try:
        os.makedirs(MARKER_DIR, exist_ok=True)
        with open(marker, "w") as fh:
            fh.write("1")
        _prune_markers()
    except OSError:
        pass
    return True


def _ask_blender(code):
    """Run read-only code in Blender. Return its result dict, or None."""
    try:
        with socket.create_connection(BRIDGE, timeout=BRIDGE_TIMEOUT) as conn:
            conn.settimeout(BRIDGE_TIMEOUT)
            payload = json.dumps(
                {"type": "execute", "code": code, "strict_json": True}
            ).encode("utf-8")
            conn.sendall(payload + b"\0")
            buf = bytearray()
            while b"\0" not in buf:
                chunk = conn.recv(65536)
                if not chunk:
                    return None
                buf.extend(chunk)
        reply = json.loads(bytes(buf[: buf.index(b"\0")]).decode("utf-8"))
    except (OSError, ValueError):
        # Blender closed, bridge not listening, or busy past the timeout.
        # Silence is correct here: this hook is an optimisation, not a gate.
        return None
    return reply.get("result") if reply.get("status") == "ok" else None


def main():
    data = json.load(sys.stdin)
    if not data.get("tool_name", "").startswith("mcp__Blender__"):
        return

    imported = bool(IMPORT_RE.search(json.dumps(data.get("tool_input", {}))))
    first = _first_touch(data.get("session_id", ""))
    if not (imported or first):
        return

    try:
        with open(DETECT_SCRIPT, encoding="utf-8") as fh:
            code = fh.read()
    except OSError:
        return

    state = _ask_blender(code)
    if not state or not state.get("needs_fix"):
        return

    detail = []
    if state.get("solid_viewports_wrong"):
        target = state.get("color_type_target")
        wrong = next(
            (v.get("color_type") for v in state.get("viewports", [])
             if v.get("shading_type") == "SOLID" and v.get("color_type") != target),
            "?",
        )
        detail.append(
            "Solid viewport(s) {} are set to color_type={!r} instead of {!r}".format(
                state["solid_viewports_wrong"], wrong, target,
            )
        )
    if state.get("meshes_without_material"):
        detail.append(
            "mesh(es) {} carry a colour attribute but have no material".format(
                state["meshes_without_material"]
            )
        )
    if state.get("meshes_with_non_colour_material"):
        detail.append(
            "mesh(es) {} have material(s) that do not read a colour attribute "
            "(ask before touching those)".format(
                [e["object"] for e in state["meshes_with_non_colour_material"]]
            )
        )

    trigger = "A PLY import just ran." if imported else "First Blender call this session."
    print(json.dumps({
        "systemMessage": "Blender is showing PLY vertex colours as grey.",
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "{trigger} Blender was queried read-only and IS currently showing "
                "colour-carrying mesh(es) as grey: {detail}. Use the `{skill}` skill "
                "to fix it, then tell the user what changed. This was measured, not "
                "guessed -- if you disagree, re-run the detection rather than "
                "assuming the scene is fine."
            ).format(trigger=trigger, detail="; ".join(detail), skill=SKILL),
        },
    }))


try:
    main()
except Exception:
    # A hook must never break the tool call it is observing.
    pass
