---
description: Migrate a type in a FOCUS solution to mirror a pattern exemplar in a REFERENCE solution — rename it, re-base it onto the base the exemplar inherits, split its extra functionalities into partials, fix every consumer, and build. The thin-derived target pattern (base owns the shared parts; the derived overrides hooks + supplies instance specifics; extras live in partials) is read from the reference's exemplar. Trivial/mechanical mirroring proceeds automatically; the base-extension strategy and the overall plan are confirmed interactively. Multi-repo aware (reuses the /gitize repo-set cache); plans everything and gates before editing; leaves edits unstaged (P15). Usage: /port-solution -f|--focus "<focus .sln/.slnx/folder>" -r|--reference "<reference .sln/.slnx/folder>" -p|--port "<source type/symbol in focus>" -t|--to "<target type = reference exemplar to mirror>"
---

The user invoked **`/port-solution`** to **migrate a type in a FOCUS solution so it mirrors a pattern
exemplar in a REFERENCE solution**. The exemplar is a *thin derived* type: a shared base owns the
common behaviour, the derived overrides a few hooks + supplies instance specifics, and each extra
concern lives in its own partial. The job re-shapes the focus's `--port` type into that same form —
**rename** it to `--to`, **re-base** it onto the base the exemplar inherits (dropping the logic now
provided by the base), **split** its remaining extras into partials, and **fix every consumer** — then
verify with a build. Distilled from the 2026-06-30 `Sistec.5315` ⟵ `Sistec.5309AB-C`
`LayoutContainer → Cell` migration. Reuses the [[gitize-command]] repo-set cache.

The governing rule: *mirror the reference exemplar's pattern exactly; mechanical mirroring proceeds
automatically, but any edit to a shared base (and the overall plan) is confirmed and gated.*

Constants / reuse:
- Repo-set discovery + cache: [[gitize-command]] Step 1 (`git-repos-<stem>` memory).
- Per P13 no Claude co-author on any commit; per **P15** leave the agent's edits **unstaged**.
- WinForms partials follow **S5** (canonical Form/Control two-file split) and **S6** (the
  `_FormViewBlocker` prepend on auxiliary partials). Code follows **S3/S4/S9**.

## 1. Parse the arguments
Flags order-independent; strip surrounding quotes. **All four are required**:
- `--focus` / `-f` `"<…>"` → the FOCUS solution (`.sln`/`.slnx`/folder) whose type is migrated.
- `--reference` / `-r` `"<…>"` → the REFERENCE solution that holds the pattern exemplar to mirror.
- `--port` / `-p` `"<…>"` → the source **type/symbol** in the focus to migrate (e.g. `LayoutContainer`).
- `--to` / `-t` `"<…>"` → the **target type name**, which is also the **reference exemplar** to mirror
  (e.g. `Cell` — the type to find in the reference whose shape the migration copies).
- Missing any of the four → print the Usage synopsis and **stop**. `-h`/`--help` anywhere → **P11**
  prints this command's parameters and does not execute (handled by the directive, not here).

## 2. Recall first (P0.2) — do not re-derive
Before reading code, recall from memory: both solutions' **repo-set caches** ([[gitize-command]]
Step-1 `git-repos-<stem>`; discover + persist if absent), any **anchor/theme memory** for the focus
and reference, and prior knowledge of the `--to` pattern. Start from what is already known; only read
genuinely new/unverified data.

## 3. Locate both sides
- **Focus** — find the `--port` type and **all** its files: the main `.cs`, the `.Designer.cs`, every
  function-isolating partial (`<Type>.*.cs`), and any `.resx`. Note its current base (often a generic
  `UserControl`/`Form`/plain class).
- **Reference** — find the `--to` exemplar and the **base** it inherits. **Key check:** is that base a
  type **shared by both solutions** (present in a common repo/namespace on each side)? If so it is the
  migration target — and renaming `--port`→`--to` typically also clears a **name collision** with that
  base. Record the base's location in *both* solutions.

## 4. Characterize the pattern (reference exemplar)
Read the `--to` exemplar (+ its Designer) and its base. Extract the target shape:
- what the **base owns** vs. what the **thin derived** supplies (the overridden hooks / virtual members,
  the constructor shape, e.g. `InitializeComponent(); WireUp();`);
- the **file split** — main (`<Type>.cs`), Designer (`<Type>.Designer.cs`), and which concerns sit in
  partials;
- for designable types: which controls the **base designer** creates (shared chrome) vs. which the
  **derived designer** creates, and how **z-order** is pinned (e.g. `Controls.SetChildIndex`).

## 5. Characterize the focus source (`--port`)
Read the `--port` type + all its partials/Designer/resx and the shared base. Classify its members into:
- **(a) base-duplicated** — logic that the shared base already provides (to be **dropped**, inherited
  instead);
- **(b) instance specifics** — the per-instance data the base exposes as hooks (routes/labels/config/
  background/etc.) → become **overrides** on the new derived type;
- **(c) extras** — functionality the base does **not** have (interfaces it implements, extra `Use(...)`
  builders, dynamic wiring) → **kept**, each cohesive concern in its **own partial**;
- **(d) base-internal extras** — (c) that can only run inside a base-private method (so a thin derived
  cannot reach it) → flags the need for a base extension point (Step 7).

## 6. Impact analysis (P0.7.f) — enumerate consumers
**Grep the focus solution** for every consumer of the `--port` symbol before editing: `new <Type>(...)`
instantiations, **field/variable declarations** of the type, **event subscriptions**, and **fluent
builder chains**. Flag what **breaks under the new inheritance** — most notably a **fluent chain** where
an inherited base method returns the *base* type and so loses access to the derived-only members called
later in the chain (→ must **reorder** so derived-returning calls precede base-returning ones, or split
the chain). Size the full blast radius; fold it into the plan.

## 7. Base-extension fork (only if Step 5(d) found base-internal extras)
When an extra must run inside a base-private method (page-creation hook, a non-virtual `Start()`-style
finaliser, …), the base needs a **`protected virtual` no-op hook** the derived can override. This
**edits the shared base** → **P1**. **Confirm via `AskUserQuestion`** which strategy:
- **focus base only** — add the hook(s) to the focus's copy of the base; **report the divergence** vs.
  the reference's base (P1);
- **both bases, kept in sync** — add the identical no-op hook(s) to **both** the focus and reference
  copies (no divergence; **note this edits the reference solution too**);
- **no base edit** — keep the affected logic in the derived (less thin; e.g. retain a local override
  path) so the base is untouched.
Hooks are empty by default (`protected virtual void OnX(...) { }`) and invoked at the right point in the
base; the derived overrides them. (If Step 5(d) found nothing, skip this fork.)

## 8. Plan + approval gate
Present the full plan and **gate** with `AskUserQuestion` (`Proceed` / adjust / plan-only) **before any
edit**: the **file ops** (rename `--port`→`--to`; the partial split; `.resx` rename), the **base edits**
(from Step 7, with the chosen scope), the **derived overrides**, the **consumer fixes** (incl. any
fluent-chain reorder), and the **verify** step. Fold the Step-7 choice in here if not already taken.

## 9. Execute (after approval)
- **Base edits first** (if chosen) — add the no-op virtual hook(s); call them at the correct point
  (e.g. after a page is cached, before a finaliser returns); apply **identically** to each base in scope.
- **Thin derived main file** (`<--to>.cs`) — constructor mirrors the exemplar; override the instance
  hooks from Step 5(b); drop all Step 5(a) duplicated logic.
- **Designer** (`<--to>.Designer.cs`) — create **only** the instance controls (+ the derived-owned
  labels); do **not** re-create controls the base designer owns; pin **z-order** via `SetChildIndex`;
  drop dead fields; set the type `Name`. Keep `InitializeComponent`/`Dispose`/`components` private per S5.
- **Partials** — move each Step 5(c) extra into its own `<--to>.<Concern>.cs`; for WinForms auxiliary
  partials prepend the **S6 `_FormViewBlocker`**. Builders that returned the old type now return `<--to>`.
- **File renames** — `mv`/`rm` via the Bash tool (plain filesystem, **NOT `git mv`/`git add`**, to stay
  unstaged per P15). Rename `<--port>.resx` → `<--to>.resx` when the csproj is **SDK-glob** (no explicit
  `<Compile>`/`<EmbeddedResource>`/`<DependentUpon>` for these files — check first); if the csproj names
  them explicitly, update those entries instead.
- **Consumers** — rename instantiations + field/variable types to `<--to>`; apply the Step-6 fixes
  (reorder/split broken fluent chains; pass named arguments if a signature shifted).

## 10. Verify + report
- **Build the focus solution** (`dotnet build <focus .sln/.slnx>`) → expect **0 errors** (note the
  pre-existing warning baseline).
- If a base in **another** solution was edited (Step 7 "both bases"), **build that project too** to
  confirm the edit is safe there.
- **Confirm every touched repo is UNSTAGED** (`git status --short` across them, P15); if an agent edit
  **slipped into the index**, `git reset HEAD -- <file>` to unstage it (keep the working-tree change).
- Report the change set, and per **P1** explicitly **report any divergence** created between the
  solutions' bases. Per **P13** no Claude co-author.

## Notes / constraints
- Read-only until the Step-8 gate; everything after is gated and left unstaged for review.
- Multi-repo: the focus type, the shared base, and the consumers can live in **different repos** — edits
  span them; track each.
- If the shared base is **not** actually shared (the exemplar's base lives only in the reference), the
  migration must also bring/reference that base — surface this at the plan gate rather than guessing.
