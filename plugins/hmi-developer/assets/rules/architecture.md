---
paths:
  - "**/*.cs"
  - "**/*.csproj"
  - "**/*.sln"
---

## Architecture & Boundaries

This solution strictly enforces dependency inversion. Inner layers CANNOT reference outer layers. Stop and ask the user for clarification if a request violates these boundaries.

| Layer | Responsibility | Dependencies |
|-------|---------------|-------------|
| **Presentation** | WinForms Forms and UserControls. ZERO business logic. | Controls & UI |
| **Controls & UI** | Reusable UI components (`TrackingViewBase<T>`, `TabContainer<T>`, `Led`, `Button`). No domain rules. | Business Logic interfaces |
| **Business Logic** | `*Logic` classes, `Watchdog`, `HandShake`. Subscribes to tags, exposes events, applies domain rules. | ITagProvider, IDevice |
| **Data Access** | `IRepositoryAsync<T>`, `IDbConnector`, Dapper.Contrib. No business rules. | Sistec.Core |
| **Communication** | `IDevice`, `OpcUaClient`, Modbus, `KrcClient`. Transport only — no business rules. | Sistec.Core |
| **Tag / Model** | `IBasicValue<T>`, `OpcUaTagValue<T>`, `MonitoredTag`, `AsyncPayload<T>`. Pure data contracts. | None |

### Layer Diagram (Sistec.HMI)

```
PRESENTATION (WinForms)
  FrmHMI, UserControls (uc2_Home, PressBrake, etc.)
       |
CONTROLS & UI
  TrackingViewBase<T>, TabContainer<T>, Led, Button, Connection
       |
BUSINESS LOGIC
  *Logic classes (BS2308Logic, PlcLogic, ModeLogic, ProgramLogic)
  Watchdog, HandShake
       |
DATA ACCESS
  IRepositoryAsync<T>, IDbConnector, Dapper.Contrib
       |
COMMUNICATION
  IDevice, OpcUaClient, Modbus, KrcClient
       |
TAG / MODEL
  IBasicValue<T>, OpcUaTagValue<T>, MonitoredTag, AsyncPayload<T>
       |
EXTERNAL SYSTEMS
  OPC UA Servers (PLCs), Modbus Devices, KUKA Robots, Database
```

### Progetti e Dipendenze (Sistec.HMI)
```
Sistec.Core (netstandard2.1)         <- Nessuna dipendenza Sistec
Sistec.Opc.Ua (netstandard2.1)      <- Sistec.Core
Kuka.Client (netstandard2.1)         <- Sistec.Core
Sistec.Controls (net8.0-windows)     <- Sistec.Core
Sistec.UI (net8.0-windows)           <- Sistec.Core, Sistec.Controls
Sistec.Common (net8.0-windows)       <- Sistec.Core, Sistec.Controls, Sistec.Opc.Ua
Sistec.Bus (net8.0-windows)          <- Sistec.Core
Sistec.5309AB (WinExe)               <- Tutti i precedenti
Sistec.5309C (WinExe)                <- Tutti i precedenti
Sistec.BS (WinExe)                   <- Tutti i precedenti
```

---

## Dependency Injection

- **Constructor injection** is the only permitted DI mechanism. Property and method injection are forbidden.
- All dependencies must be injected through the constructor and stored as `private readonly` fields.
- Prefer interfaces over concrete types for all injected dependencies.
- **No service locator pattern.** Do not use `IServiceProvider` or `ServiceLocator` in application code.
- Register services with the minimum lifetime required: `Transient` > `Scoped` > `Singleton`.
