# Inline comments — judgment rules

For `//` comments inside method bodies and non-public code. XML `///` contract rules live in SKILL.md / wording.md.

Contents: 1. The gate · 2. Comments worth writing · 3. Comment smells · 4. Annotation tokens · 5. Drift prevention · 6. Examples

## 1. The gate (run per comment, in order)

1. Is the code self-explanatory as written? → no comment.
2. Would a better name or an extracted method remove the need? → prefer the refactor; if out of scope for this change, flag it instead of papering over it with prose.
3. Does the comment explain WHY (constraint, decision, rejected alternative) rather than WHAT? → only then write it.
4. Will it still help a maintainer after the next refactor? → keep it tied to things that survive (constants, issue links, invariants).

Supplementary test — *mental bookkeeping*: a comment also earns its place when it compacts hidden state the reader would otherwise reconstruct (e.g. annotating accumulated protocol state across a call sequence). Facts alone don't qualify; reconstruction cost does.

## 2. Comments worth writing (mandatory categories)

- Non-obvious invariants and ordering constraints ("order matters: must match the PLC structure layout").
- Workarounds, with a tracking link: `// HACK: retry once — driver drops first read after reconnect. Remove after #142.`
- Performance-motivated shape that looks simplifiable but isn't.
- Magic values whose meaning no name carries (better: extract the constant, comment the constant once).
- Concurrency/thread-safety reasoning (why this lock, why this ordering, why fire-and-forget is safe here).
- Deliberately empty or surprising blocks — an empty `catch` must say why it is empty.
- Multi-step hardware/protocol sequences: numbered `// STEP 1:`, `// STEP 2:` comments, one per phase.

## 3. Comment smells (do not write; remove on sight during a doc pass)

- **Redundant**: restates the adjacent line (`i++; // increment i`).
- **Paraphrased name**: summary-style comment repeating the method name in different words.
- **Journal**: dated changelog entries — version control owns history.
- **Commented-out code**: delete it; git remembers.
- **Noise markers**: `// end of loop`, decorative separators (unless the host style uses `#region` deliberately).
- **Stale**: contradicts the code. During any pass, a wrong comment outranks a missing one as a defect — fix or delete it, and say so in the report.

## 4. Annotation tokens (fixed vocabulary)

`TODO`, `HACK`, `UNDONE` are recognized by the Visual Studio Task List (Ctrl+\, T). Keep the set small and consistent with the host project; default meanings:

| Token | Meaning | Format |
|---|---|---|
| TODO | Planned, not blocking | `// TODO(owner): action — context/issue` |
| HACK | Works, wrong on purpose | `// HACK: why + removal condition/issue` |
| UNDONE | Reverted/incomplete work | `// UNDONE: what remains` |

An annotation without an action, owner, or exit condition is a smell, not a plan.

## 5. Drift prevention

- Reference symbols, don't duplicate values: `// waits up to ReadTimeoutMs` not `// waits up to 5 seconds`. Duplicated values silently rot when the constant changes.
- Date or condition anything that expires ("Remove after firmware 2.4 ships").
- Keep the comment adjacent to what it explains; a comment separated from its code by later edits is half-rotten already.

## 6. Examples

Bad → good:

```csharp
// check if connected
if (!_session.Connected) return AsyncPayload<Tag>.Fail();          // BAD: restates WHAT

// Session drops silently on PLC power-cycle; reconnect is owned by the watchdog,
// so a dead session here must fail fast instead of retrying.
if (!_session.Connected) return AsyncPayload<Tag>.Fail();          // GOOD: WHY
```

```csharp
// increase counter by one
_retries++;                                                        // BAD: noise

// Third retry gives ~1.5 s total at the 500 ms poll rate — the PLC's worst-case boot gap.
if (_retries > MaxRetries) throw new DeviceUnreachableException(_device.Name);  // GOOD: justifies the constant
```
