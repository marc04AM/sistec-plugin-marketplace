---
paths:
  - "**/*.cs"
---

## Event Patterns

### Declaration
Custom delegate types defined in `Delegates.cs`:
```csharp
public event OneParamEventHandler<bool> ResetCompleted;
public event EventHandler? ValueChanged;
public event EventHandlerAsync2<TrackingPayload>? EditRequest;
public event CancelEventHandler? OnClearRequest;
public event PropertyChangedEventHandler? PropertyChanged;
```

### Custom Delegates (`Sistec.Core/Delegates.cs`)
```csharp
public delegate void OneParamEventHandler<T>(T value);
public delegate Task OneParamEventHandlerAsync<T>(T value);
public delegate void TwoParamEventHandler<T1, T2>(T1 value1, T2 value2);
public delegate Task EventHandlerAsync(object sender, EventArgs e);
public delegate Task<bool> EventHandlerAsync2<T>(object sender, T eventArgs);
public delegate void NoParamEventHandler();
public delegate Task<AsyncPayload<T>> QueryResultAsync<T>(object sender);
```

Prefer delegates (`Func<>`, `Action<>`, `Predicate<>`) over single-method interfaces for strategy injection, callbacks, and pipeline composition:
```csharp
// GOOD: delegate injection
public class OrderProcessor(Func<Order, decimal> calculateDiscount)
{
    public decimal Process(Order order) => calculateDiscount(order);
}

// AVOID: single-method interface when a delegate suffices
public interface IDiscountCalculator { decimal Calculate(Order order); }
```
Use interfaces when the contract involves multiple methods, requires state, or needs explicit mocking in tests.

### Raising Events
```csharp
Change?.Invoke(this, new(this));
ResetCompleted?.Invoke(true);
PropertyChanged?.Invoke(this, new(propertyName));
```

### Protected Virtual OnXxx Pattern
```csharp
protected virtual void OnValueChanged(EventArgs e) => ValueChanged?.Invoke(this, e);
protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
    => PropertyChanged?.Invoke(this, new(propertyName));
```

### Subscription
```csharp
// Lambda
StateColors.AddingNew += (s, e) => _addingNew = true;

// Named method
odometer.SourceChanged += OnSourceChanged;

// Unsubscription
odometer.SourceChanged -= OnSourceChanged;
```

### Event Subscription Safety
**NEVER** re-attach an event handler that was detached by another part of the business logic. The detachment is intentional and part of the application's behavioral contract. Document subscription/unsubscription points with `<remarks>` explaining the lifecycle. Prefer weak event patterns or explicit `IDisposable`-based subscription management to prevent leaks.
