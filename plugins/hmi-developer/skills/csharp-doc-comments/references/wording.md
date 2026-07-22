# Canonical wording — Microsoft .NET API documentation templates

Source: dotnet/dotnet-api-docs wiki + StyleCop SA16xx. Use the exact template; fill the placeholders. All doc text: starts with a capital letter, ends with a period (SA1629), no self-referential type/member names inside a summary (exceptions: constructors and Dispose).

Contents: 1. Summaries · 2. Returns · 3. Parameters · 4. Property `<value>` · 5. Exceptions · 6. Property/accessor matching · 7. Overloads · 8. Copy-paste rule

## 1. Summaries per member kind

| Member kind | Template |
|---|---|
| Class (general) | Present-tense third-person verb clause: "Represents …" / "Provides …" |
| Interface | "Defines …" / "Provides …" / "Exposes …" |
| Abstract base class | "Defines the core behavior of X and provides a base for derived classes." |
| Sealed/static class | Verb-first summary + "This class cannot be inherited." |
| Exception class | "The exception that is thrown when X." (does NOT start with a verb) |
| Constructor (class) | "Initializes a new instance of the `<see cref="X"/>` class." |
| Constructor (struct/record struct) | "Initializes a new instance of the `<see cref="X"/>` struct." |
| Static constructor | "Initializes static members of the `<see cref="X"/>` class." |
| Method (general) | Present-tense third-person verb clause. Add information: not "Formats a string" but what is replaced/produced. |
| Async / Task-returning method | "Asynchronously *verbs* *object*." |
| `Dispose()` | "Releases the resources used by the current instance of the X class." |
| `Dispose(bool)` | "Called by the Dispose() and Finalize() methods to release the managed and unmanaged resources used by the current instance of the X class." |
| Method that always throws | "Throws a/an X exception in all cases." (explain why in `<remarks>`) |
| Property get+set | "Gets or sets X." |
| Property get+set bool | "Gets or sets a value indicating whether X." |
| Property get-only | "Gets X." (never write "this property is read-only") |
| Property get-only bool | "Gets a value indicating whether X." |
| Property get+init | "Gets X." or "Gets or initializes X." |
| Enum type | "Specifies X." / "Describes X." |
| Enum member | Noun phrase. Bit-mask member: "A mask used to retrieve X." |
| Event | "Occurs when X." |
| `XEventArgs` class | "Provides data for the X event." |
| Event-handler delegate | "Represents the callback method that will handle the X event of a Y." |
| `OnX` method | "Raises the X event." |
| Operator (unary/binary) | Present-tense verb clause: "Adds …", "Compares …" |
| Conversion operator | "Converts a X to a Y." |
| Abstract/virtual member | "When overridden in a derived class, *verb clause*." |
| Extension block / extension class | "Defines a set of extension members for X." |

## 2. `<returns>` per return kind

| Return kind | Template |
|---|---|
| `Task<T>` / `ValueTask<T>` | "A task that represents the asynchronous operation. The task result contains X." (equivalently: "A task object that, when awaited, produces X.") |
| `bool` | "`<see langword="true"/>` if X; otherwise, `<see langword="false"/>`." (never "true to …") |
| Flags enum | "A bitwise combination of the enumeration values that X." |
| Other enum | "One of the enumeration values that X." |
| Class/interface/struct/primitive/string | Noun phrase with article, without the type name: "The number of bytes read." |
| Array | "An array that contains X." |
| Method that always throws | "This method doesn't return a value." |

## 3. `<param>` per parameter kind

| Parameter kind | Template |
|---|---|
| `bool` | "`<see langword="true"/>` to X; otherwise, `<see langword="false"/>`." — note: "true **to**", the opposite of the return convention |
| Flags enum | "A bitwise combination of the enumeration values that X." |
| Other enum | "One of the enumeration values that X." |
| Index (int) | "The zero-based index of X." |
| `ref` | "*Description*, passed by reference." |
| `out` | "When this method returns, contains X. This parameter is treated as uninitialized." |
| Array | "An array that contains X." |
| Everything else | Noun phrase with article, no type name; state purpose and valid range when constrained. |

## 4. `<value>` (properties)

- Template: noun phrase + "The default is X." when a default exists and matters.
- Bool: "`<see langword="true"/>` if X; otherwise, `<see langword="false"/>`. The default is X." (returns-style "if", not parameter-style "to")
- State measurement units ("in milliseconds", "in bytes") when relevant. Never bury the default only in `<remarks>`.

## 5. Exceptions

- Condition phrased as if preceded by "if", present tense: `<exception cref="ArgumentException">The device name is empty.</exception>`
- Null argument: `<paramref name="x"/> is <see langword="null"/>.`
- Multiple independent conditions, same exception type: one sentence per condition, joined by a line containing exactly `-or-`.
- Exception that always fires: condition text is "In all cases."
- Task-returning methods where the exception lands on the task: append "This exception is stored into the returned task."
- Document every exception thrown directly by the member; add nested ones only when callers realistically hit them. Never invent.

## 6. Property/accessor matching (SA1623/SA1624)

- get-only ⇒ starts "Gets"; set-only ⇒ "Sets"; get+set ⇒ "Gets or sets"; bool adds "a value indicating whether".
- Restricted setter (e.g. `public string Name { get; private set; }`): omit "or sets" — unless the setter is protected/protected internal (a derived class always sees it), or its access equals the property's effective visibility.

## 7. Overloads

Write one summary concept broad enough for all overloads, then differentiate each overload's own summary by what distinguishes it (the extra parameter, the format, the culture). Do not copy one overload's summary verbatim onto another.

## 8. Copy-paste rule (SA1625)

No two doc-text blocks inside one member may be identical. Sole exception: genuinely unused parameters may all read "The parameter is not used."
