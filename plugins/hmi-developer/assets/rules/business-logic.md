---
paths:
  - "**/*Logic*.cs"
  - "**/HandShake*.cs"
  - "**/Watchdog*.cs"
---

## Logic Class Architecture

Standard pattern for `*Logic` classes:
1. Receive `ITagProvider` in constructor
2. Subscribe to tags in constructor
3. Use local functions for event handlers
4. Expose events for external notification

```csharp
public class BS2308Logic
{
    public BS2308Logic(ITagProvider tagProvider)
    {
        var status = tagProvider.GetTag<ushort>("Stato")!;
        status.SourceChanged += OnStatusChanged;
        OnStatusChanged(status);  // Init with current value

        return;

        void OnStatusChanged(IBasicValue<ushort> tag)
        {
            var value = (PunchingStatus)(tag?.Value ?? 0xFFFF);
            if (Status == value) return;
            Status = value;
            IsRunning = value == PunchingStatus.Running;
        }
    }
}
```

---

## Handshake Pattern (PLC Communication)

Two symmetrical variants in `HandShake.cs`:

**PlcToHmi** (PLC signals, HMI confirms):
1. Wait signal TRUE -> 2. Set ACK TRUE -> 3. Wait signal FALSE -> 4. Set ACK FALSE

**HmiToPlc** (HMI commands, PLC confirms):
1. Set command TRUE -> 2. Wait ACK TRUE -> 3. Set command FALSE -> 4. Wait ACK FALSE

Characteristics: signal-based wake-up (no polling), linked CancellationTokenSource for composite timeouts, logging at every transition, deterministic resource cleanup.

---

## Tag Subscription Pattern

```csharp
// Init: create tag, subscribe, call handler with current value
var tag = tagProvider.GetTag<ushort>("TagName")!;
tag.SourceChanged += OnTagChanged;
OnTagChanged(tag);  // Important: init with current value

return;
void OnTagChanged(IBasicValue<ushort> tag) => Property = tag?.Value ?? default;
```

---

## Layered Flow

A user action flows **WinForms event -> Logic class -> Repository/Device** and returns through the same path. No layer may skip an intermediate layer. A Form must never call `IRepositoryAsync<T>` directly — it delegates to a `*Logic` class.
