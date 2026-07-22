# Tag selection, modern constructs, compiler warnings

Contents: 1. Tag decision table · 2. Syntax notes · 3. `<inheritdoc/>` · 4. Records & primary constructors · 5. Other modern constructs · 6. Compiler doc warnings · 7. Enabling validation

## 1. Tag decision table

| Situation | Tag(s) |
|---|---|
| Any public type or member | `<summary>` — bare minimum |
| Parameters (methods/ctors/indexers/delegates) | `<param name="x">` per parameter |
| Non-void return | `<returns>` |
| Generic type/method | `<typeparam name="T">` per type parameter |
| Throwable exception (verified) | `<exception cref="Type">condition</exception>` |
| Property semantic description | `<value>` (in addition to the `<summary>`) |
| Parameter/type-parameter named in prose | `<paramref name="x"/>` / `<typeparamref name="T"/>` |
| Cross-reference to code | `<see cref="Member"/>` inline; `<seealso cref="Member"/>` for a See-Also section (not nestable inside `<summary>`) |
| External link | `<see href="url">text</see>` — `cref` never makes URLs clickable |
| Keyword/literal (`null`, `true`, `false`, `async`, `sealed`) | `<see langword="null"/>` |
| Inline code fragment | `<c>…</c>`; multi-line sample: `<example><code>…</code></example>` |
| Multi-paragraph text | `<para>` per paragraph inside summary/remarks/returns |
| Bulleted/numbered/table content | `<list type="bullet|number|table">` (never raw markdown) |
| Supplemental info (algorithms, business rules, usage constraints) | `<remarks>` — only when non-obvious |
| Override / interface implementation | `<inheritdoc/>` (see §3) |
| Doc text maintained in a separate XML file | `<include file='…' path='…'/>` |
| Deprecation | `[Obsolete("Use X instead")]` attribute — never doc-comment prose |
| Deferred work | `// TODO:` inline comment — never an XML tag |

## 2. Syntax notes

- Generic cref: brace form `cref="List{T}"`, `cref="IDictionary{TKey, TValue}"` (compiler treats `{}` as `<>`).
- Disambiguate overloads in cref with a parameter list: `cref="Parse(string)"`, else CS0419 (ambiguous reference).
- Literal `<`/`>` in prose: `&lt;` / `&gt;`.
- `///` on every line; Visual Studio scaffolds `<summary>` automatically on typing `///`.
- Doc comments are not metadata: not embedded in the assembly, not reachable via reflection; consumers read the sibling `.xml` file.

## 3. `<inheritdoc/>`

Valid on types, interface implementations, overrides, constructors.

- Interface implementation and method override: bare `<inheritdoc/>`.
- Reuse a sibling's docs (sync ↔ async twin): `<inheritdoc cref="Parse(string)"/>`.
- Partial inheritance: `path` XPath filter, e.g. `<inheritdoc cref="X" path="/returns"/>`.
- Explicit tags on the member always win; inheritance only fills gaps.

Pitfalls:

1. Visual Studio shows inherited docs in IntelliSense even with NO tag — but the compiled XML file stays empty for that member. Always write the tag on public members.
2. Inherited `<param>` requires the parameter name to match the base exactly; a mismatch fails silently.
3. Documenting some parameters and inheriting the rest still fires CS1573 — inherit all or document all.
4. `<inheritdoc/>` on a member with nothing to inherit from is itself a violation (SA1648).
5. Inheriting from a generic interface may not render in DocFX — verify in the doc pipeline if one is used.

## 4. Records & primary constructors

- Positional record / primary constructor (C# 12): document the parameters with `<param>` tags on the **type declaration**:

```csharp
/// <summary>
/// Represents an OPC UA node subscription request.
/// </summary>
/// <param name="NodeId">The fully qualified node identifier.</param>
/// <param name="Interval">The sampling interval, in milliseconds.</param>
public sealed record Subscription(string NodeId, int Interval);
```

- There is no tag yet for the compiler-synthesized properties themselves; the `<param>` on the declaration is the official mechanism.
- Known gap: a class with a primary constructor cannot carry a type-level `<summary>` distinct from the constructor's — VS hover shows the constructor doc. For public API types that need both, consider a conventional constructor.

## 5. Other modern constructs

- `required` members: standard property wording applies; put "must be set during initialization" nuance in `<remarks>` if needed (no official summary convention exists).
- Nullable annotations (`T?`): nullability lives in the signature; document only behavioral consequences (e.g. "-or- `<see langword="null"/>` if no device is connected." in `<returns>`).
- Extension members: summary + `<param>` for the receiver on the block/class; individual members document only their own tags.

## 6. Compiler doc warnings

| Warning | Meaning | Fix |
|---|---|---|
| CS1591 | Public member lacks any XML comment (fires only with doc file generation on) | Add `<summary>` or `<inheritdoc/>` |
| CS1572 | `<param>` names a parameter that doesn't exist | Rename/delete the tag |
| CS1573 | Some parameters documented, others not | Document all (or inherit all) |
| CS1734 | `<paramref>` names a nonexistent parameter | Fix the name (check partial declarations use identical names) |
| CS0419 | Ambiguous `cref` (overloads) | Qualify: `cref="F(int)"` |

## 7. Enabling validation

- `<GenerateDocumentationFile>true</GenerateDocumentationFile>` in the csproj emits `<assembly>.xml` and turns on CS1591.
- StyleCop severities configurable per rule: `dotnet_diagnostic.SA1600.severity = warning` in `.editorconfig`.
- Scoped suppression when a project legitimately opts out: `#pragma warning disable CS1591` … `restore`, never a blanket project-wide silence without a stated reason.
