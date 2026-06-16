---
paths:
  - "**/Frm*.cs"
  - "**/frm*.cs"
  - "**/uc*.cs"
  - "**/*.Designer.cs"
  - "**/Controls/**/*.cs"
  - "**/UI/**/*.cs"
---

## WinForms & UI Conventions

### Form Lifecycle
```csharp
[STAThread]
private static void Main()
{
    // 1. Translation init
    TranslationExtensions.Translations.Locale = Settings.Default.Locale;
    // 2. Singleton check
    if (Utilities.AlreadyRunning()) { ... return; }
    // 3. Global exception handlers
    AppDomain.CurrentDomain.UnhandledException += Utilities.CurrentDomain_UnhandledException;
    Application.ThreadException += Utilities.Application_ThreadException;
    // 4. Configuration
    Configuration.Configure();
    // 5. Logger setup
    SpvLog = Utilities.CreateLogger(Utilities.GetFileName(Configuration.LogPath, $"{name}_.log"));
    // 6. Health check loop (DB + PLC connectivity)
    while (true) { ... if (info.Valid) break; }
    // 7. Main form
    Application.EnableVisualStyles();
    Application.SetCompatibleTextRenderingDefault(false);
    Application.Run(new FrmHMI(name));
}
```

### Control Naming Conventions
For controls directly related to a domain variable, name the control after the variable:
```csharp
// domain variable: program
// corresponding GroupBox: grpProgram
GroupBox grpProgram;
```

| Prefix | Control Type | Example |
|--------|-------------|---------|
| `btn` | Button | `btnOk`, `btnReset`, `btnDownload` |
| `lbl` | Label | `lblStatus`, `lblMode`, `lblWarning` |
| `txt` | TextBox | `txtValue` |
| `chk` | CheckBox | `chkEnabled` |
| `cmb` | ComboBox | `cmbProgram` |
| `grp` | GroupBox | `grpState`, `grpTitle` |
| `pnl` | Panel | `pnlContainer` |
| `uc` | UserControl | `uc2_Home`, `uc4_Info` |
| `led` | LED indicator | `ledStatus` |
| `lbAlarm` | Alarm label | `lbAlarm1`, `lbAlarm2` |
| `UC` | Main container | `UC2`, `LowerPanel` |

### DataBinding Pattern
```csharp
btnDownload.DataBindings.Add("Enabled", _buttonsStatus,
    "ButtonDownloadEnabled", true, DataSourceUpdateMode.OnPropertyChanged);
```

### ISupportInitialize
```csharp
public class Led : UserControl, ISupportInitialize
{
    public void BeginInit() { _initializing = true; }
    public void EndInit() { _initializing = false; SetState(_state); }
}
```

### Thread Safety (UI)
```csharp
// SafeInvoke extension
this.SafeInvoke(() => ledStatus.Blinking = true);

// InvokeRequired pattern
protected override void UpdateControls()
{
    if (InvokeRequired) { Invoke(UpdateControls); return; }
    // Actual UI update
}
```

### WndProc Override
```csharp
protected override void WndProc(ref Message m)
{
    base.WndProc(ref m);
    const int WM_NCHITTEST = 0x0084;
    const int HTTRANSPARENT = -1;
    if (m.Msg == WM_NCHITTEST && EventTransparent)
        m.Result = (IntPtr)HTTRANSPARENT;
}
```

### Designer Pattern
```csharp
partial class FrmHMI
{
    private IContainer components = null;

    protected override void Dispose(bool disposing)
    {
        if (disposing && (components != null)) components.Dispose();
        base.Dispose(disposing);
    }

    #region Windows Form Designer generated code
    private void InitializeComponent()
    {
        // ...
        UC2.SuspendLayout();
        SuspendLayout();
        // control assignments
        UC2.ResumeLayout(false);
        ResumeLayout(false);
    }
    #endregion
}
```

---

## Controls & Custom Controls

### Custom Control Base Classes
- `TrackingViewBase<T>`: base for tracking views, binds to `ITrackingInfo` data
- `TabContainer<T>`: composite container for tabbed tracking panels
- `Led`: LED indicator with blinking support, implements `ISupportInitialize`
- `Button`: extended button with `ActionRequest` event and `IsClean` state

### Led Control Pattern
```csharp
public class Led : UserControl, ISupportInitialize
{
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

    public LedColor ActiveColor { get; set; } = LedColor.Green;
    public LedColor InactiveColor { get; set; } = LedColor.Gray;
}
```

### EventTransparent Pattern
Controls that should be click-through use `WndProc` override:
```csharp
public bool EventTransparent { get => _eventTransparent ?? false; }

protected override void WndProc(ref Message m)
{
    base.WndProc(ref m);
    const int WM_NCHITTEST = 0x0084;
    const int HTTRANSPARENT = -1;
    if (m.Msg == WM_NCHITTEST && EventTransparent)
        m.Result = (IntPtr)HTTRANSPARENT;
}
```

---

## Dialog Patterns

### DialogTemplate<T>
- Path: `Sistec.HMI/Common/Dialogs/DialogTemplate.cs`
- Constraint: `where T : UserControl, IContainedControl`
- Always-on-top via WndProc override
- Button enable/disable tied to `IsDirty`

### IContainedControl Interface
```csharp
public Size CalculatedSize { get; }
public bool IsDirty { get; set; }
public event EventHandler<bool>? IsDirtyChanged;
public void Closing();
```

### Static Factory Methods for Dialogs
```csharp
DialogTemplate<T>.Show(containedControl, message, title, buttons);
DialogTemplate<T>.ShowDialog(containedControl, message, title, buttons);
FrmWait.ShowWaitWindow(owner);
```

---

## Translation & Localization

```csharp
// Init in control constructor
TranslationExtensions.WhenTranslationsReady(
    () => TranslationExtensions.BindTranslations(Translate)
);

// Translate method with InvokeRequired guard
protected virtual void Translate(ITranslations t)
{
    if (InvokeRequired)
    {
        Invoke(new OneParamEventHandler<ITranslations>(Translate), t);
        return;
    }
    lblStatus.Text = t.Get(_status);
    grpTitle.Text = t.Get(_title);
}
```

Translation key format: `"ClassName_ControlName"` or `"#description"`. Use `GetOrDefault()` for fallback values.
