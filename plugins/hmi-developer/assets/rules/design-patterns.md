---
paths:
  - "**/*.cs"
---

## Design Patterns

### Observer Pattern
Primary pattern for tag value notification:
```csharp
event TagChangedDelegate<T> SourceChanged;  // Triggered from BUS source
event TagChangedDelegate<T> TagChanged;     // Triggered from tag value change

var idPart = tagProvider.GetTag<ushort>("ID_PART")!;
idPart.SourceChanged += OnIdPartChanged;
```

### Factory Pattern
```csharp
// Static factory method with validation on a domain class
public static AsyncPayload<ProductionConfig> Create(int id, string commessa)
{
    if (string.IsNullOrWhiteSpace(commessa))
        return AsyncPayload<ProductionConfig>.Fail();
    if (id < 0)
        return AsyncPayload<ProductionConfig>.Fail();
    return AsyncPayload<ProductionConfig>.Success(new ProductionConfig { Id = id, Commessa = commessa });
}

private ProductionConfig() { }
```

Rules:
- Prefer `static Create(...)` factory methods with validation that return `AsyncPayload<T>`.
- Use dedicated `Factory` classes when construction requires external dependencies.
- Constructors must be `private` or `internal` when a factory method exists.
- `TagFactory` / `OpcUaTagFactory` for generic tag creation. `PageFactory` for dynamic UI pages. `DialogTemplate<T>.Show()` for dialogs.

### Builder / Fluent API Pattern
```csharp
tracking
    .Use(tagProvider.GetTag<int>("ID_Batch"), "ID Batch", false)
    .Use(logger)
    .Use(clearTag, ackTag)
    .Start();
```
Each `Use()` method returns `this` for chaining.

### Strategy Pattern
```csharp
public interface IReconnectionPolicy
{
    int InitialDelay { get; set; }
    int MaxDelay { get; set; }
    bool ShouldReconnect { get; }
    int NextDelay(double attempts);
}
// Implementations: ExponentialBackoffReconnectionPolicy, NoReconnectionPolicy
```

### Repository Pattern
```csharp
public interface IRepositoryAsync<T> where T : class
{
    Task<AsyncPayload<bool>> DeleteAsync(T entity);
    Task<AsyncPayload<IEnumerable<T>>> GetAllAsync();
    Task<AsyncPayload<IEnumerable<T>>> GetAsync(string whereString, object parameters);
    Task<AsyncPayload<T>> GetAsync(object id);
    Task<AsyncPayload<int>> InsertAsync(T entity);
    Task<AsyncPayload<bool>> UpdateAsync(T entity);
}
```

### Template Method Pattern
```csharp
public abstract class AbstractPropertyContainer : INotifyPropertyChanged
{
    protected bool SetField<T>(ref T field, T value, [CallerMemberName] string propertyName = "")
    {
        if (EqualityComparer<T>.Default.Equals(field, value)) return false;
        field = value;
        LastChanged = DateTime.Now;
        SafePropertyChanged(propertyName);
        return true;
    }
}
```

### Composite Pattern
```csharp
public class TabContainer<T> : ISizeable where T : ITrackingInfo
{
    private readonly TabContainerLogic<T> _logic;
    private readonly IDictionary<int, ITracking> _panels;
}
```
