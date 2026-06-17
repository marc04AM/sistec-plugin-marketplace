#!/usr/bin/env python3
# Extract every POU's declaration + implementation from the PLCopen XML produced
# by the CODESYS export (export_project.py), decoding ST, SFC and LD bodies.
#
# Python 3 IS available on this machine, so this uses xml.etree.ElementTree --
# the natural choice. itertext() flattens the mixed-namespace XHTML fragments
# that PowerShell's DOM InnerText could not handle (see process.md, steps 12-16).
#
# Usage:
#   python extract_pous.py <exported_source.xml> <out_dir> <consolidated_path>
#
# Outputs:
#   <out_dir>\<PouName>.txt   one file per POU (declaration + decoded body + actions)
#   <consolidated_path>       every POU concatenated into one file
#
# Each per-POU file contains:
#   === POU: <name> (<pouType>) ===
#   --- DECLARATION ---    (plain-text VAR block from <InterfaceAsPlainText>)
#   --- IMPLEMENTATION --- ([<lang>] + the decoded main body)
#   --- ACTIONS ---        (each <action> body, decoded; only if present)
#   --- TRANSITIONS ---    (each <transition> body, decoded; only if present)
#
# Body decoding:
#   * ST  -> the structured-text source verbatim.
#   * SFC -> steps (initial marked) with their action blocks (qualifier + ref),
#            and the step->transition->step flow with resolved transition
#            conditions, handling selection/simultaneous divergences & jumps.
#   * LD  -> per network, each coil / output resolved back through the contact
#            chain (AND = series, OR = parallel), function-block calls and inline
#            expressions. FBD is rendered with the same network resolver.
# SFC action/transition references resolve to the bodies listed in the ACTIONS /
# TRANSITIONS sections of the same POU.

import os
import sys
import datetime
import xml.etree.ElementTree as ET


# --------------------------------------------------------------------------- #
# Generic XML helpers
# --------------------------------------------------------------------------- #
def local(tag):
    """Tag name without its {namespace} prefix."""
    return tag.rsplit('}', 1)[-1] if '}' in tag else tag


def find_local(elem, name):
    """First descendant (self included) whose local tag name == name, else None."""
    if local(elem.tag) == name:
        return elem
    for e in elem.iter():
        if local(e.tag) == name:
            return e
    return None


def child(elem, name):
    """First DIRECT child with local tag name == name, else None."""
    if elem is None:
        return None
    for c in elem:
        if local(c.tag) == name:
            return c
    return None


def children(elem, name):
    """All DIRECT children with local tag name == name."""
    if elem is None:
        return []
    return [c for c in elem if local(c.tag) == name]


def text_of(elem):
    """Trimmed .text of an element (empty if None)."""
    if elem is None or elem.text is None:
        return ''
    return elem.text.strip()


def one_line(s):
    """Collapse all whitespace to single spaces (for inline condition labels)."""
    return ' '.join((s or '').split())


def xhtml_text(container):
    """Flattened text of the first <xhtml> under `container` (empty if none)."""
    if container is None:
        return ''
    x = find_local(container, 'xhtml')
    if x is None:
        return ''
    return ''.join(x.itertext()).strip()


def in_refs(elem):
    """refLocalIds from this element's DIRECT <connectionPointIn> children."""
    refs = []
    for cpi in children(elem, 'connectionPointIn'):
        for conn in children(cpi, 'connection'):
            r = conn.get('refLocalId')
            if r is not None:
                refs.append(r)
    return refs


# --------------------------------------------------------------------------- #
# SFC decoder
# --------------------------------------------------------------------------- #
SFC_FLOW = {'step', 'transition', 'jumpStep',
            'selectionDivergence', 'simultaneousDivergence',
            'selectionConvergence', 'simultaneousConvergence'}


def render_sfc(sfc, action_names, trans_names):
    # Index every element that carries a localId (the SFC children are flat).
    elements = {}
    for e in sfc:
        lid = e.get('localId')
        if lid is not None:
            elements[lid] = e

    def kind(i):
        return local(elements[i].tag) if i in elements else '?'

    # Step -> [(qualifier, reference-name)] from the action blocks attached to it.
    step_actions = {}
    for ab in children(sfc, 'actionBlock'):
        acts = []
        for a in children(ab, 'action'):
            q = a.get('qualifier') or 'N'
            ref = child(a, 'reference')
            if ref is not None:
                nm = ref.get('name') or '?'
            else:
                inline = one_line(xhtml_text(a))
                nm = '(inline: %s)' % inline if inline else '(inline)'
            acts.append((q, nm))
        for s in in_refs(ab):
            step_actions.setdefault(s, []).extend(acts)

    # Forward flow edges: predecessor-id -> [successor-id] (document order).
    edges = {}
    for lid, e in elements.items():
        if local(e.tag) in SFC_FLOW:
            for r in in_refs(e):
                edges.setdefault(r, []).append(lid)

    def cond_ref(trans):
        cpi = child(child(trans, 'condition'), 'connectionPointIn')
        conn = child(cpi, 'connection')
        return conn.get('refLocalId') if conn is not None else None

    def resolve_cond(trans):
        r = cond_ref(trans)
        if r is not None and r in elements and kind(r) == 'inVariable':
            expr = one_line(text_of(child(elements[r], 'expression')))
            if expr in trans_names:
                return '%s (-> transition %s)' % (expr, expr)
            return expr or '?'
        inline = one_line(xhtml_text(child(trans, 'condition')))
        return inline or '?'

    # Collapse transitions/divergences so each step maps to (conds, target) edges.
    def successors(step_id):
        out = []

        def rec(node, conds, parallel, seen):
            for succ in edges.get(node, []):
                k = kind(succ)
                if succ in seen:
                    if k == 'step':
                        out.append((conds, parallel,
                                    elements[succ].get('name', '?') + ' (loop)'))
                    continue
                nxt = seen | {succ}
                if k == 'step':
                    out.append((conds, parallel, elements[succ].get('name', '?')))
                elif k == 'jumpStep':
                    out.append((conds, parallel,
                                'JUMP -> ' + (elements[succ].get('targetName') or '?')))
                elif k == 'transition':
                    rec(succ, conds + [resolve_cond(elements[succ])], parallel, nxt)
                elif k == 'simultaneousDivergence':
                    rec(succ, conds, True, nxt)
                else:  # selection div/conv, simultaneous conv -> pass through
                    rec(succ, conds, parallel, nxt)

        rec(step_id, [], False, {step_id})
        return out

    lines = ['Steps:']
    for s in children(sfc, 'step'):
        sid = s.get('localId')
        init = s.get('initialStep') == 'true'
        lines.append('  %s %s%s' % ('-', s.get('name', '?'),
                                    '  (INITIAL)' if init else ''))
        for q, nm in step_actions.get(sid, []):
            ann = ''
            base = nm.split('.')[0]
            if nm in action_names or base in action_names:
                ann = '  (-> action %s)' % nm
            lines.append('        %-2s %s%s' % (q, nm, ann))

    lines.append('Flow:')
    any_flow = False
    for s in children(sfc, 'step'):
        succ = successors(s.get('localId'))
        if not succ:
            continue
        any_flow = True
        lines.append('  %s:' % s.get('name', '?'))
        for conds, parallel, target in succ:
            ctxt = ' & '.join('(%s)' % c for c in conds) if conds else 'TRUE'
            tag = '  [parallel]' if parallel else ''
            lines.append('      --[ %s ]--> %s%s' % (ctxt, target, tag))
    if not any_flow:
        lines.append('  (no transitions)')

    return '\n'.join(lines)


# --------------------------------------------------------------------------- #
# LD / FBD decoder
# --------------------------------------------------------------------------- #
def _is_networktitle(elem):
    for d in elem.iter():
        if local(d.tag) == 'ElementType' and (d.text or '').strip() == 'networktitle':
            return True
    return False


def render_ld(root_elem, lang):
    elems = {}
    ordered = []
    for e in root_elem:
        lid = e.get('localId')
        if lid is not None:
            elems[lid] = e
            ordered.append(e)

    def kind(i):
        return local(elems[i].tag) if i in elems else '?'

    def varname(e):
        return text_of(child(e, 'variable')) or '?'

    def block_call(e, seen):
        args = []
        inv = child(e, 'inputVariables')
        for v in children(inv, 'variable'):
            fp = v.get('formalParameter') or ''
            val = resolve_inputs(v, seen)
            if val is None:
                val = 'TRUE'  # connected straight to the power rail
            args.append('%s:=%s' % (fp, val) if fp else val)
        ty = e.get('typeName') or 'BLOCK'
        inst = e.get('instanceName')
        head = '%s(%s)' % (ty, ', '.join(args))
        return '%s {%s}' % (head, inst) if inst else head

    def resolve_conn(conn, seen):
        r = conn.get('refLocalId')
        fp = conn.get('formalParameter')
        v = resolve(r, seen)
        if v is None:
            return None
        if fp and fp not in ('', 'none') and kind(r) == 'block':
            return '%s.%s' % (v, fp)
        return v

    def resolve_inputs(e, seen):
        parts = []
        for cpi in children(e, 'connectionPointIn'):
            for conn in children(cpi, 'connection'):
                p = resolve_conn(conn, seen)
                if p:
                    parts.append(p)
        if not parts:
            return None
        if len(parts) == 1:
            return parts[0]
        return '(' + ' OR '.join(parts) + ')'

    def resolve(i, seen):
        if i not in elems:
            return None
        if i in seen:
            return '<...>'
        seen = seen | {i}
        e = elems[i]
        k = local(e.tag)
        if k == 'leftPowerRail':
            return None
        if k == 'inVariable':
            return text_of(child(e, 'expression')) or '?'
        if k == 'contact':
            inx = resolve_inputs(e, seen)
            term = ('NOT ' if e.get('negated') == 'true' else '') + varname(e)
            return (inx + ' AND ' + term) if inx else term
        if k in ('coil', 'outVariable'):
            return resolve_inputs(e, seen)
        if k == 'block':
            return block_call(e, seen)
        return '<%s>' % k

    # Split into networks at each network-title marker; rails/comments are global.
    networks = []
    cur = []
    for e in ordered:
        k = local(e.tag)
        if k == 'vendorElement' and _is_networktitle(e):
            if cur:
                networks.append(cur)
            cur = []
        elif k in ('leftPowerRail', 'rightPowerRail', 'comment', 'vendorElement'):
            continue
        else:
            cur.append(e)
    if cur:
        networks.append(cur)

    out = []
    for ni, net in enumerate(networks, 1):
        out.append('Network %d:' % ni)
        rendered = False
        for e in net:
            k = local(e.tag)
            if k == 'coil':
                pfx = {'set': '(S) ', 'reset': '(R) '}.get(e.get('storage'), '')
                out.append('  %s%s := %s' %
                           (pfx, varname(e), resolve_inputs(e, set()) or 'TRUE'))
                rendered = True
            elif k == 'outVariable':
                out.append('  %s := %s' %
                           (text_of(child(e, 'expression')) or '?',
                            resolve_inputs(e, set()) or 'TRUE'))
                rendered = True
        # Blocks that assign directly through an output expression.
        for e in net:
            if local(e.tag) != 'block':
                continue
            for v in children(child(e, 'outputVariables'), 'variable'):
                cpo = child(v, 'connectionPointOut')
                tgt = text_of(child(cpo, 'expression'))
                if tgt:
                    fp = v.get('formalParameter') or ''
                    suffix = '.' + fp if fp and fp != 'ENO' else ''
                    out.append('  %s := %s%s' % (tgt, block_call(e, set()), suffix))
                    rendered = True
        if not rendered:
            for e in net:
                if local(e.tag) == 'block':
                    out.append('  %s' % block_call(e, set()))
                    rendered = True
        if not rendered:
            out.append('  (no output elements)')

    return '\n'.join(out) if out else '[empty %s body]' % lang


# --------------------------------------------------------------------------- #
# Body dispatch + POU assembly
# --------------------------------------------------------------------------- #
LANG_TAGS = ('ST', 'SFC', 'LD', 'FBD', 'IL', 'CFC')


def decode_body(body, action_names, trans_names):
    """Return (lang, decoded-text) for a <body> element."""
    if body is None:
        return ('-', '[no body]')
    lang_elem = None
    for c in body:
        if local(c.tag) in LANG_TAGS:
            lang_elem = c
            break
    if lang_elem is None:
        return ('-', '[implementation not extracted]')
    lang = local(lang_elem.tag)
    if lang == 'ST':
        return ('ST', xhtml_text(lang_elem) or '[empty ST body]')
    if lang == 'SFC':
        return ('SFC', render_sfc(lang_elem, action_names, trans_names))
    if lang in ('LD', 'FBD'):
        return (lang, render_ld(lang_elem, lang))
    return (lang, '[%s body present but not decoded]' % lang)


def get_decl(pou):
    ipt = find_local(pou, 'InterfaceAsPlainText')
    if ipt is None:
        return '[declaration not available as plain text]'
    return xhtml_text(ipt)


def render_pou(pou):
    name = pou.get('name') or '<unnamed>'
    pou_type = pou.get('pouType') or '?'

    actions = children(child(pou, 'actions'), 'action')
    transitions = children(child(pou, 'transitions'), 'transition')
    action_names = set(a.get('name') for a in actions if a.get('name'))
    trans_names = set(t.get('name') for t in transitions if t.get('name'))

    decl = get_decl(pou)
    lang, impl = decode_body(child(pou, 'body'), action_names, trans_names)

    parts = ["=== POU: %s (%s) ===\n" % (name, pou_type),
             "--- DECLARATION ---\n%s\n" % decl,
             "--- IMPLEMENTATION ---\n[%s]\n%s\n" % (lang, impl)]

    if actions:
        sect = ["--- ACTIONS (%d) ---" % len(actions)]
        for a in actions:
            alang, atext = decode_body(child(a, 'body'), action_names, trans_names)
            sect.append("\n### action: %s  [%s]\n%s" % (a.get('name') or '?', alang, atext))
        parts.append('\n'.join(sect) + '\n')

    if transitions:
        sect = ["--- TRANSITIONS (%d) ---" % len(transitions)]
        for t in transitions:
            tlang, ttext = decode_body(child(t, 'body'), action_names, trans_names)
            sect.append("\n### transition: %s  [%s]\n%s" % (t.get('name') or '?', tlang, ttext))
        parts.append('\n'.join(sect) + '\n')

    return name, '\n'.join(parts)


def main():
    if len(sys.argv) != 4:
        sys.stderr.write("usage: extract_pous.py <xml> <out_dir> <consolidated_path>\n")
        return 2

    xml_path, out_dir, consolidated_path = sys.argv[1], sys.argv[2], sys.argv[3]
    if not os.path.isfile(xml_path):
        sys.stderr.write("XML not found: %s\n" % xml_path)
        return 1

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    cons_dir = os.path.dirname(consolidated_path)
    if cons_dir and not os.path.isdir(cons_dir):
        os.makedirs(cons_dir)

    tree = ET.parse(xml_path)
    root = tree.getroot()

    pous = [e for e in root.iter() if local(e.tag) == 'pou']
    names = []
    for pou in pous:
        name, text = render_pou(pou)
        with open(os.path.join(out_dir, name + '.txt'), 'w', encoding='utf-8') as f:
            f.write(text)
        names.append(name)

    # Consolidated single-file copy: every POU concatenated, alphabetical for stable diffs.
    with open(consolidated_path, 'w', encoding='utf-8') as cf:
        cf.write("# Consolidated PLC source - %d POUs\n" % len(names))
        cf.write("# Source XML: %s\n" % xml_path)
        cf.write("# Generated:  %s\n\n" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        for n in sorted(names):
            p = os.path.join(out_dir, n + '.txt')
            if os.path.isfile(p):
                with open(p, 'r', encoding='utf-8') as pf:
                    cf.write(pf.read())
                cf.write("\n")

    print("Extracted %d POUs to %s" % (len(names), out_dir))
    print("Consolidated source: %s" % consolidated_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
