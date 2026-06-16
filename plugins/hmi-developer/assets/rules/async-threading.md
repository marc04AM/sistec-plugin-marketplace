---
paths:
  - "**/*.cs"
---

## Async Patterns

**Rule:** I/O operations must be `async`, suffixed with `Async`, and pass `CancellationToken`. Prefer `ValueTask<T>` where synchronous completion is likely.

### Task-Based Async
```csharp
public async Task<HMI> Bind(IOpcuaIO client, int scanInterval = 100, LogFunction log = null)
public async Task<AsyncPayload<int>> InsertAsync(CutPlan entity)
public static async Task<bool> ResetHandshake(IBasicValue<Odometer> odometer, CancellationToken cancel)
```

### CancellationToken Composition
```csharp
var timeoutCts = new CancellationTokenSource(timeout);
var changeCts = new CancellationTokenSource();
var cts = CancellationTokenSource.CreateLinkedTokenSource(cancel, timeoutCts.Token, changeCts.Token);
```

### Fire-and-Forget (`TaskExtensions.cs`)
```csharp
public static void Forget(this Task task)
{
    if (!task.IsCompleted || task.IsFaulted)
    {
        _ = ForgetAwaited(task);
    }

    static async Task ForgetAwaited(Task task)
    {
        try { await task.ConfigureAwait(false); }
        catch { }
    }
}

// Usage
Watch().Forget();
```

### ConfigureAwait(false)
Use in library code to avoid SynchronizationContext issues:
```csharp
await task.ConfigureAwait(false);
```

### Async Event Handler in UI
```csharp
private async void btnCleanProgram_ActionRequest(Sistec.Controls.Button value)
{
    _buttonsStatus.IsCleanEnabled = false;
    var e = new CancelEventArgs(false);
    CleanProgramRequest?.Invoke(this, e);
    if (e.Cancel) { ... return; }
    // async operation
}
```

---

## Thread Safety

### SafeInvoke Extension
```csharp
public static void SafeInvoke(this Control control, Action action)

this.SafeInvoke(() => ledStatus.Blinking = true);
```

### SynchronizationContext
```csharp
public SynchronizationContext SynchronizationContext { get; set; }

protected void SafeInvoke(Action action)
    => SynchronizationContext?.Post(o => action(), null);
```

### Lock-Based Synchronization
```csharp
private readonly object _lock = new();
lock (_lock)
{
    if (_error) return;
    _error = true;
}
```

### ConcurrentDictionary
```csharp
private readonly ConcurrentDictionary<NodeId, MonitoredTag> _forwarding = new();
```
