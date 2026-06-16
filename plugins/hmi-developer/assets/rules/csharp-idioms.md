---
paths:
  - "**/*.cs"
---

## String Handling

### String Interpolation (Preferred)
```csharp
var name = $"SPV_{Settings.Default.Commessa}";
$"{robot.IPAddress}:{robot.Port}{(robot.Enabled ? "" : get("DisabledSuffix"))}"
$"Bind{nameof(HMI)} type {typeof(T)}"
```

### string.Format
Rare, used for localization:
```csharp
string.Format(get("DiagnosticsTemplate"), PopupButtons.Ok);
```

### DateTime Formatting
```csharp
$"[{DateTime.Now:HH:mm:ss.fff}] {context} progress: {details}\r\n"
```

---

## Null Handling

**Rule:** `<Nullable>enable</Nullable>` is active. Treat warnings as errors. Avoid the null-forgiving operator (`!`).

### Pattern Matching
```csharp
if (obj is Odometer other) { ... }
```

### Null-Coalescing
```csharp
var alternateBackColor = alternateBackColor ?? Color.LightGray;
public bool EventTransparent { get => _eventTransparent ?? false; }
```

### Guard Clauses (Early Return)
```csharp
if (value == _currentValue) return;
if (!p.IsSuccess) return;
if (_mode == null) throw new InvalidCastException(...);
```

### Null-Conditional for Tag Values
```csharp
var value = (PunchingStatus)(tag?.Value ?? 0xFFFF);
var value = tag?.Value ?? false;
```

---

## Property Patterns

### Auto-Properties (Preferred for Simple Properties)
```csharp
public float AbsoluteValue { get; set; }
public LedColor InactiveColor { get; set; } = LedColor.Gray;
protected MainStation Main { get; private set; }
```

### Expression-Bodied (Getter Only)
```csharp
public string Info => $"{count}/{Capacity}";
public bool IsFull => Capacity != 0 && count >= Capacity;
public bool IsAuto => Mode == SistecModeEnum.Automatic;
```

### Full Properties with Backing Field
old code implemented before switching to c# 12
For validation, side effects, or change notification:
```csharp
private bool _active;
public bool Active {
    get => _active;
    set {
        if (_active == value) return;
        _active = value;
        Blinking = false;
        Color = _active ? ActiveColor : InactiveColor;
    }
}
```

### Properties with `field` Keyword (C# 12)
new properties **must** be written using this convention
```csharp
public bool IsDirty {
    get;
    set {
        if (field == value) return;
        field = value;
        IsDirtyChanged?.Invoke(this, value);
    }
}
```

### Initialization at Declaration
```csharp
public BindingList<BlinkColor> BlinkColors { get; } = [];
public readonly Dictionary<string, PropertyNotifierT<T>> Notifiers = [];
```

### Collections
Return `IReadOnlyList<T>` or `IReadOnlyCollection<T>`. Use `.Any()` instead of `.Count > 0`.

---

## Generics & Constraints

```csharp
public interface IRepositoryAsync<T> where T : class
public class ModeLogic<T> : AbstractPropertyContainer where T : IStation
public class TabContainer<T> : ISizeable where T : ITrackingInfo
public class DialogTemplate<T> : Form where T : UserControl, IContainedControl

// Interface composition
public interface ILXM32 : IInverter, IMotionEncoder, ILimitSwitch { }

// Generic methods
public IBasicValue<T>? GetTag<T>(string name)
protected bool SetField<T>(ref T field, T value, [CallerMemberName] string propertyName = "")
```

---

## Modern C# Features

### Always use **var** keyword where it's possible
```csharp
var x = 1; // prefer this
int y = 2; // not this
```

### Target-Typed New (C# 9+)
```csharp
private readonly OpcUaClientCollection _opcUaClientCollection = new();
public BindingList<BlinkColor> BlinkColors { get; } = [];
```

### Pattern Matching
```csharp
if (obj is Odometer other) { ... }
catch (TaskCanceledException) when (changeCts.IsCancellationRequested) { }

switch ((value1, value2))
{
    case (false, false): ...
    case (true, false): ...
}
```

### Expression-Bodied Members
```csharp
public void Clear() => text.Clear();
public decimal Constrain(decimal value) =>
    value < _minimum ? _minimum : value > _maximum ? _maximum : value;
```

### Fluent LINQ (Non Query Syntax)
```csharp
var tags = Tags.Values.Where(x => x.TagInfo.Type == typeof(T));
var result = BlinkColors.Select(x => (int)x.Interval).ToList();
```

### Local Functions (Post-return)
```csharp
public BS2308Logic(ITagProvider tagProvider)
{
    var status = tagProvider.GetTag<ushort>("Stato")!;
    status.SourceChanged += OnStatusChanged;
    OnStatusChanged(status);

    return;

    void OnStatusChanged(IBasicValue<ushort> tag) { ... }
    void OnIdBatchChanged(IBasicValue<int> tag) => ID_Batch = tag?.Value ?? 0;
}
```

### `field` Keyword (C# 12)
```csharp
public bool CanReconnect {
    get;
    set { field = value; btnReconnect.Enabled = value; }
}
```

### Tuple Deconstruction
```csharp
foreach (var (_, plc) in Configuration.PlcConfig) { }
```

---

## General Coding Principles

### No Reflection
**DO NOT** use `System.Reflection`, `dynamic`, `Activator.CreateInstance`, or `Type.GetMethod` in application code.
- Use generics (`T`) and constraints (`where T : IEntity`) instead of runtime type discovery.
- Use pattern matching (`is`, `switch` expressions) instead of runtime type checks.
- Use interfaces and polymorphism instead of `MethodInfo.Invoke`.
- **Exception:** Reflection is tolerable only inside infrastructure-level framework code (e.g., custom DI registration, EF Core configuration scanning) and must be documented with `<remarks>`.

### OOP + Functional Programming — No Procedural Code

**Absolute rule:** zero procedural code. This applies to every file, every change, every snippet.

Banned patterns:
- Standalone helper methods with no owning object: `CopyJobDataFields()`, `BuildDto()`, `MapToEntity()`
- `static` utility/helper classes (bags of functions)
- Imperative `for`/`foreach` when a LINQ pipeline or functional composition is equivalent
- Methods that mutate a parameter passed by reference ("output parameter" style)
- Anemic domain models: classes with only `{ get; set; }` properties and zero behavior

**OOP for structure:** encapsulation, polymorphism, and inheritance model domain boundaries and enforce invariants. Domain rules live inside the entity or value object that owns the data — not in a separate `*Helper` or `*Util` class.

**FP for behavior:** pure functions (no side-effects), immutability, and composition for all data transformations. Side-effects (I/O, DB, logging) are pushed to the edges; core logic stays pure and testable.

**DDD style (Zoran Horvat):**
- Value objects are `record` types with `private` constructors and a `static Create(...)` factory that returns `AsyncPayload<T>`
- Entities expose behavior methods that return new state rather than mutating in place
- `CopyJobDataFields(source, dest)` → wrong. The entity exposes `job.WithUpdatedFields(source)` that returns a new instance
- Collections on domain objects are `IReadOnlyList<T>`; mutation goes through explicit domain methods

```csharp
// WRONG — procedural helper
static void CopyJobDataFields(Job source, Job dest)
{
    dest.Name = source.Name;
    dest.Quantity = source.Quantity;
}

// RIGHT — behavior on the domain object
public record Job(string Name, int Quantity)
{
    public Job WithFields(Job source) => this with { Name = source.Name, Quantity = source.Quantity };
}
```

```csharp
// WRONG — imperative loop
var names = new List<string>();
foreach (var job in jobs)
    if (job.IsActive) names.Add(job.Name);

// RIGHT — declarative pipeline
var names = jobs.Where(j => j.IsActive).Select(j => j.Name).ToList();
```

Keep side-effects (I/O, DB, logging) at the edges; core domain logic must remain pure and testable.

### Minimal Scope
- Declare variables at the point of first use, inside the innermost block.
- Prefer local functions over private methods when the logic is used by a single caller.
- Keep methods short: target a maximum of ~20 lines of logic.
- Avoid class-level fields when a local variable or method parameter suffices.
- Use `static` on local functions and lambdas that do not capture enclosing state.

### Memoization
```csharp
private readonly ConcurrentDictionary<string, ExpensiveResult> _cache = new();

public ExpensiveResult GetOrCompute(string key)
    => _cache.GetOrAdd(key, k => ComputeExpensiveResult(k));
```
- Use `Lazy<T>` for single-value deferred initialization.
- **NEVER** memoize methods with side-effects (I/O, DB writes, event emissions).
- Define a clear eviction or expiration strategy. Unbounded caches are memory leaks.

### Data Proximity (Fail-Fast, Fail-Safe)
- **No premature computation:** do not calculate a value 50 lines before it is needed.
- **Minimize variable lifetime:** the fewer lines between declaration and consumption, the easier the code is to reason about.
- **Fail-fast:** validate inputs at the earliest possible moment.
- **Fail-safe:** when a failure is detected, return a safe default or explicit error immediately. Never silently continue with corrupted data.
