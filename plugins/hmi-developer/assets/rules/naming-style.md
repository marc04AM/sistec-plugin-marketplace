---
paths:
  - "**/*.cs"
---

## Naming Conventions

**Rule:** `PascalCase` for Classes/Methods/Properties. `_camelCase` for private fields. `camelCase` for variables and parameters. `UPPER_CASE` for constants.

### Classes and Types
- **PascalCase**: `HMI`, `Odometer`, `Led`, `NumericInput`, `TabContainer<T>`
- Form classes with lowercase `frm` prefix: `frmOtherAdvancedSettings`, `frmLoadJobs`, `frmWait`
- Exception: main form uses PascalCase: `FrmHMI`, `FrmWait`
- **UserControl class names**: PascalCase, no prefix — `ProgressView`, `SafetyView`, `PressBrake`, `Led`, `Button`
- **UserControl field/variable names** (Designer or code): `uc` prefix — `uc2_Home`, `uc4_Info`

### Methods and Properties
- **PascalCase**: `OnProgress()`, `GetConnection()`, `SetState()`
- Event handlers: `[ControlName]_[EventName]()` or `[EventName]_[ControlName]()`
  - `FrmOtherAdvancedSettings_Load()`, `BtnOk_Click()`, `Colors_ListChanged()`

### Private Fields
- `_` + camelCase prefix: `_active`, `_blinker`, `_currentValue`, `_initializing`
- Readonly fields follow the same convention: `private readonly int _invalid = -1;`

### Constants
- **UPPER_CASE** with underscore: `DEFAULT_DECIMAL_PLACES`, `MAX_DECIMAL_PLACES`, `PANEL_WIDTH`
- Inline Win32 constants: `const int WM_NCHITTEST = 0x0084;`

### Enums
```csharp
public enum UserLevel { NoUser, Operator, Maintenance, Expert, Sistec }
public enum Priority { Info, Warning, Alarm, Critical }
public enum SistecModeEnum { NotDefined, Manual, Stop, Automatic }
```

### Interfaces
- `I` + PascalCase prefix: `IDbConnector`, `IRepositoryAsync<T>`, `ITracking`, `IDevice`, `IBasicValue<T>`

### Summary Table

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | `HMI`, `Odometer`, `BS2308Logic` |
| Forms | `frm` + PascalCase | `frmOtherAdvancedSettings` |
| Methods | PascalCase | `GetConnection()`, `OnProgress()` |
| Private fields | `_` + camelCase | `_active`, `_blinker` |
| Constants | UPPER_CASE | `MAX_DECIMAL_PLACES`, `PANEL_WIDTH` |
| Enums | PascalCase (type and values) | `UserLevel.Operator` |
| Interfaces | `I` + PascalCase | `IDbConnector`, `ITracking` |
| Parameters | camelCase | `string context` |
| UI Controls | abbreviated prefix | `btn*`, `lbl*`, `txt*`, `led*` |
| UserControl (class name) | PascalCase, no prefix | `ProgressView`, `SafetyView` |
| UserControl (instance/field) | `uc` + index/name | `uc2_Home`, `uc4_Info` |

---

## Code Formatting

### Indentation
- **Tab** (equivalent to 4 spaces), consistent across all files and projects.

### Brace Style
- **Opening brace on same line** for properties and short blocks:
  ```csharp
  public bool Active {
      get => _active; set { ... }
  }
  ```
- **Allman style** for methods and classes:
  ```csharp
  public class Led : UserControl
  {
      // ...
  }
  ```

### Single-line Statements
- Single-instruction blocks on same line without braces (early return only):
  ```csharp
  if (_active == value) return;
  if (!p.IsSuccess) return;
  ```
- All other `if-else` blocks **must** use braces:
  ```csharp
  if (condition)
  {
      doSomething;
  }
  else
  {
      doOther;
  }
  ```

### Spacing
- 1 blank line between properties/fields and methods.
- 1-2 blank lines between logical sections within a method.
- No blank lines between consecutive properties or consecutive fields.

### Line Length
- No hard limit; typically 100-120 characters.
- Long parameter lists break to multiple lines:
  ```csharp
  info.Add(new Record(robot.Description,
      $"{robot.IPAddress}:{robot.Port}{(robot.Enabled ? "" : get("DisabledSuffix"))}",
      robot.Enabled && Network.Ping(robot.IPAddress)));
  ```

---

## Commenting Style

### XML Documentation
Mandatory on all public and protected members:
```csharp
/// <summary>
/// Calculates the discounted price for a given order line.
/// </summary>
/// <param name="orderLine">The order line to evaluate.</param>
/// <param name="discountRate">Discount rate as a decimal (e.g., 0.15 for 15%).</param>
/// <returns>The final price after discount, or zero if the line is invalid.</returns>
/// <exception cref="ArgumentOutOfRangeException">Thrown when <paramref name="discountRate"/> is negative.</exception>
/// <remarks>
/// This method applies the company standard rounding policy (MidpointRounding.AwayFromZero).
/// </remarks>
public decimal CalculateDiscountedPrice(OrderLine orderLine, decimal discountRate)
```

Rules:
- `<summary>`: mandatory on all public and protected members. One sentence, imperative mood.
- `<param>`: mandatory for every parameter. Describe purpose and valid range.
- `<returns>`: mandatory on non-void methods. Describe return value and edge cases.
- `<exception>`: list every exception the method can throw with its condition.
- `<remarks>`: optional. Use only for non-obvious behavior, algorithms, or business rules.
- Internal/private members: `<summary>` only, when intent is not self-evident from the name.
- Use `/// <inheritdoc/>` to inherit documentation.
- `<remarks>` tag also used for communication direction: `/// <remarks>HMI -> PLC</remarks>`

### Comments
- **Minimize comments.** Add them only to explain **why**, never **what**.
- Use `//` single-line format for inline notes:
  ```csharp
  // order matters: use the same order used in the codesys structure
  // ignore
  catch (TaskCanceledException) when (changeCts.IsCancellationRequested) { }
  ```
- Multi-step protocol comments:
  ```csharp
  // STEP 1: Wait for signal to become TRUE
  // STEP 2: Send acknowledgment
  // STEP 3: Wait for signal to become FALSE
  ```

### Language
- Always use English: both for internal comments, business names, public APIs and technical documentation.

---

## File Organization

### One Type Per File
- One public class/interface per file. File name = class name: `Odometer.cs` contains `class Odometer`.

### Partial Classes
Heavy use for large classes, especially `FrmHMI`:
```
FrmHMI.cs                          - Main initialization
FrmHMI.Designer.cs                 - Auto-generated UI
FrmHMI.Close.cs                    - Shutdown logic
FrmHMI.DB.cs                       - Database operations
FrmHMI.Log.cs                      - Logging
FrmHMI.Plc.cs                      - PLC communication
FrmHMI.Program.cs                  - Program loading
FrmHMI.Program.OnLoadProgram.cs    - Program load flow
FrmHMI.Program.ValidateConfiguration.cs
FrmHMI.PageChange.cs               - Navigation
FrmHMI.PageChange.Routes.cs        - Routes
FrmHMI.PageChange.Tracking.cs      - Tracking UI
FrmHMI.Popups.cs                   - Dialog management
FrmHMI.PressBrake.cs               - Press brake control
```
Partial classes **group related functionality**, not just Designer files.

### Member Order Within File
1. Using directives
2. Namespace declaration
3. Class declaration with inheritance/interfaces
4. Constants and private readonly fields
5. Private fields
6. Public properties
7. Constructors
8. Public methods
9. Protected/private methods
10. Event handlers
11. Nested types (if any)

### Regions
Used only in auto-generated Designer files:
```csharp
#region Windows Form Designer generated code
#endregion
```

### Preprocessor Directives
```csharp
//#define HIDE_SPLASH_LOG
#define USE_SECONDARY_SCREEN

#if DEBUG && USE_SECONDARY_SCREEN
    // Debug-only code
#endif
```

---

## Using Directives

### Order
1. System namespaces (`System`, `System.Collections`, `System.Linq`)
2. Third-party libraries (`Dapper`, `ProtoBuf`, `Serilog`, `Opc.Ua`)
3. Project namespaces (`Sistec.*`)

### Aliases
```csharp
using IEncoder = Opc.Ua.IEncoder;
using ATV320 = Sistec.Controls.Motors.ATV320;
```

### Global Usings
Not used extensively; prefer file-specific imports. Auto-generated `*.GlobalUsings.g.cs` present.

---

## Access Modifiers

### Always Explicit
```csharp
public class Led : UserControl, ISupportInitialize { }
private delegate void WndProcDelegate(ref Message m);
protected MainStation Main { get; private set; }
internal static class Program { }
```

### Standard Order
`[visibility] [static/readonly/async] [type] [name]`
```csharp
public async Task<HMI> Bind(...)
private readonly OpcUaClientCollection _opcUaClientCollection = new();
protected bool ChangingText { get; set; }
public static async Task<bool> ResetHandshake(...)
```

### readonly vs const
- `readonly` for runtime-initialized values:
  ```csharp
  private readonly int Invalid = -1;
  public readonly TimeSpan NewPartReadDataDelay = TimeSpan.FromMilliseconds(1500);
  ```
- `const` for compile-time constants:
  ```csharp
  const int WM_NCHITTEST = 0x0084;
  public const int DefaultMaxLength = 5500;
  ```
