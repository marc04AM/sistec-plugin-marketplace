---
paths:
  - "**/Repository*.cs"
  - "**/DbConnector*.cs"
  - "**/OpcUa*.cs"
  - "**/Modbus*.cs"
  - "**/Krc*.cs"
  - "**/Kuka*.cs"
---

## DTO & Serialization

### Protobuf Records
```csharp
[ProtoContract]
public record ATV320 : IATV320dto
{
    public ATV320() { }

    public ATV320(IATV320dto template)
    {
        IN_AlarmInhibit = template.IN_AlarmInhibit;
    }

    [ProtoMember(1)]
    public bool IN_AlarmInhibit { get; private set; }
}
```

### Records, Immutability & Collections
```csharp
// GOOD: immutable record + collection search
public record OrderSummary(string CustomerId, IReadOnlyList<OrderLine> Lines)
{
    public decimal Total => Lines.Sum(l => l.Price * l.Quantity);
    public IReadOnlyList<OrderLine> HighValue => Lines.Where(l => l.Price > 100).ToList();
}
```

Rules:
- Prefer `record` for reference-type DTOs, commands, queries, and value objects.
- Prefer `record struct` for small, stack-allocated value types (≤ 4 fields, no heap references).
- All data structures **immutable by default**. Use `init`-only setters. Mutability requires explicit justification.
- Use `IReadOnlyList<T>`, `IReadOnlyCollection<T>`, or `ImmutableArray<T>` for public-facing collections.

---

## Database Access

- **ORM**: Dapper.Contrib
- **Abstraction**: `IDbConnector` / `DbConnector`
- **Pattern**: Repository with `AsyncPayload<T>`

```csharp
public class JobRepositoryAsync : IRepositoryAsync<Job>
{
    private readonly IDbConnector _db;

    public JobRepositoryAsync(IDbConnector db) => _db = db;

    public async Task<AsyncPayload<IEnumerable<Job>>> GetAllAsync()
    {
        try
        {
            var result = await _db.GetConnection().GetAllAsync<Job>();
            return AsyncPayload<IEnumerable<Job>>.Success(result);
        }
        catch (Exception e)
        {
            return AsyncPayload<IEnumerable<Job>>.Fail(e);
        }
    }
}
```

---

## Communication Patterns

### OPC UA
- Client: `OpcUaClient` with subscription-based monitoring
- Tag values: `OpcUaTagValue<T>` implements `IBasicValue<T>`
- Factory: `OpcUaTagFactory.Create<T>(nodeId, log)`
- Reconnection: `ExponentialBackoffReconnectionPolicy`
- Thread-safe: `ConcurrentDictionary<NodeId, MonitoredTag>`

### Tag Registration Flow
```csharp
// 1. Init tags
var hmi = new HMI();
hmi.Init(root);

// 2. Bind to OPC UA client
await hmi.Bind(opcUaClient, scanInterval: 100, log);

// 3. Inside Bind: register + activate
var registered = await client.RegisterTagsAsync(tags.Select(...));
var count = await client.ActivateSubscriptionsAsync();
```

### Other Protocols
- **Modbus**: EasyModbus library (press brake / Gade)
- **KUKA Robot**: `Kuka.Client` (netstandard2.1), `IRobotLogic` interface
