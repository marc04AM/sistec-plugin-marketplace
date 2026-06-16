---
paths:
  - "**/*.cs"
---

## Error Handling

**Rule:** DO NOT use exceptions for control flow. Use a Result pattern (`Result<T>` or `AsyncPayload<T>`) for application logic failures.

### AsyncPayload<T> (Railway-Oriented Programming)
```csharp
public struct AsyncPayload<T>
{
    public bool IsSuccess { get; set; }
    public T? Value { get; set; }
    public Exception? Exception { get; set; }
    public bool IsException => Exception != null;

    public static AsyncPayload<T> Fail() => new();
    public static AsyncPayload<T> Fail(Exception e) => new(e);
    public static AsyncPayload<T> Success(T value) => new(value);
}

// Typical usage
public async Task<AsyncPayload<IEnumerable<Job>>> GetAllAsync()
{
    try
    {
        var result = await DB.GetConnection().GetAllAsync<Job>();
        return AsyncPayload<IEnumerable<Job>>.Success(result);
    }
    catch (Exception e)
    {
        return AsyncPayload<IEnumerable<Job>>.Fail(e);
    }
}

if (!p.IsSuccess) return;
```

### Functional Composition (Map / Bind)
Extend `AsyncPayload<T>` with these two methods to enable railway-oriented chaining without nested `if (!p.IsSuccess)` checks:

```csharp
// Map: transform the value when successful, propagate failure unchanged
public AsyncPayload<TOut> Map<TOut>(Func<T, TOut> transform)
    => IsSuccess ? AsyncPayload<TOut>.Success(transform(Value!)) : AsyncPayload<TOut>.Fail(Exception!);

// Bind: chain an operation that itself returns AsyncPayload (flatMap)
public AsyncPayload<TOut> Bind<TOut>(Func<T, AsyncPayload<TOut>> next)
    => IsSuccess ? next(Value!) : AsyncPayload<TOut>.Fail(Exception!);

// Async variants
public async Task<AsyncPayload<TOut>> MapAsync<TOut>(Func<T, Task<TOut>> transform)
    => IsSuccess
        ? AsyncPayload<TOut>.Success(await transform(Value!).ConfigureAwait(false))
        : AsyncPayload<TOut>.Fail(Exception!);

public async Task<AsyncPayload<TOut>> BindAsync<TOut>(Func<T, Task<AsyncPayload<TOut>>> next)
    => IsSuccess
        ? await next(Value!).ConfigureAwait(false)
        : AsyncPayload<TOut>.Fail(Exception!);
```

Usage — pipeline without nested guards:
```csharp
var result = await repo.GetAsync(id)
    .MapAsync(plan => plan with { Status = PlanStatus.Active })
    .BindAsync(plan => repo.UpdateAsync(plan));

if (!result.IsSuccess) return;
```

### Validation Guards (Fail-Fast)
All precondition checks MUST appear at the top of the method, before any business logic:
```csharp
public async Task<AsyncPayload<CutPlan>> SaveAsync(CutPlan plan, IDbConnector db)
{
    // --- Guard clauses ---
    if (plan is null) return AsyncPayload<CutPlan>.Fail();
    if (db is null) return AsyncPayload<CutPlan>.Fail();
    if (!plan.Lines.Any()) return AsyncPayload<CutPlan>.Fail();

    // --- Happy path ---
    var result = await new CutPlanRepositoryAsync(db).InsertAsync(plan);
    if (!result.IsSuccess) return AsyncPayload<CutPlan>.Fail(result.Exception);
    return AsyncPayload<CutPlan>.Success(plan);
}
```

Rules:
- Group all guard clauses at the method entry point. No validation scattered through the method body.
- The "happy path" code must never be nested inside validation conditionals.

### Custom Exceptions
```csharp
public class TagException : Exception { }
public class ErrorExitException : Exception { }  // Fatal OPC UA errors
```

### Filtered Catch
```csharp
catch (TaskCanceledException) when (changeCts.IsCancellationRequested) { /* ignore */ }
catch (TaskCanceledException) when (timeoutCts.IsCancellationRequested) { /* timeout */ }
```

---

## Logging

- **Framework**: Serilog for file logging, `ISistecLogger<T>` for structured application logging.

```csharp
// Serilog direct
SpvLog.Information("Log message");

// Nullable logger (preferred)
Utilities.Logger?.Debug($"Watchdog({Name}) OnError read OK");

// LogFunction delegate
log?.Invoke("Bind", $"Registered {registered}/{tags.Count} tags");

// ISistecLogger
_logger?.Debug($"{Name}_Changed");
_logger?.Error($"{Name}_Changed: {string.Join("\r\n", result)}");
```

### Standard Log Points
- Start/end of operations: `BEGIN` / `DONE`
- State transitions
- Errors with context
- Tag binding (bound/not bound count)
- Assembly version on startup
