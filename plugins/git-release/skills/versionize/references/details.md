# versionize — background and edge cases

Read this only when the script output raises a question the SKILL.md doesn't answer.

## Why the youngest build, and not the root `release\` folder

The solution-root `release\` tree is often a stale *published* copy: on the first real run its
DLLs were ~10 days older than the project build and predated HEAD. So the script follows each
executable project's `<OutputPath>`/`<OutDir>`/`<BaseOutputPath>` and picks the subfolder with
the newest DLL.

Sistec apps set `OutputPath = bin\$(Configuration)\$(_ProductFolderName)\` with
`_ProductFolderName = "HMI v$(_AsmVerMajorMinor)"` (e.g. `bin\Release\HMI v3.25\`). The script
doesn't evaluate MSBuild. It substitutes `$(Configuration)` = Release, cuts the path at the first
remaining `$(`, and enumerates the subfolders below it (depth ≤ 2). With no redirection it falls
back to `bin\Release`, then `bin\Debug`.

## Version fields

- `version` = `AssemblyName.GetAssemblyName(dll).Version`, the real 4-part build number
  (e.g. `2.10.9652.21350`). The `.csproj` literal is often the unexpanded `3.25.*`, so never use it
  when a DLL exists.
- `sha` = the `+<sha>` suffix of `ProductVersion`, the commit the DLL was built from. It may
  predate HEAD, and the script reports that under `preflight.stale`.
- `file` = `FileVersion`, used for third-party packages whose AssemblyVersion is pinned
  (e.g. Opc.Ua).
- Cells AB and C are built separately, so shared libs can carry different build numbers per
  cell. Show both when they differ.

## Assemblies the note covers

The script keeps DLLs matching `Sistec*`, `Esa*`, `EasyModbus*`, `Kuka*`, `Opc.Ua*`,
`OPCFoundation*`, `Abc.Zebus*`, `MySql*`, `MySqlConnector*`, `MySqlBackup*`, `Dapper*`, plus the
app itself. Everything else is only counted (`other`). Usual mapping to repos: `Sistec.KRC.Client`
→ Kuka.Client repo, `EasyModbus` (AssemblyTitle `Sistec.Modbus`) → Modbus repo.

Package families for the Versions section: **Opc.Ua** (`OPCFoundation.NetStandard.Opc.Ua.*`),
**Abc** (`Abc.Zebus`, `Abc.Zebus.Contracts`), **Mysql** (`MySqlConnector`, `MySqlBackup.NET`,
`MySql.Data`), **Dapper** (`Dapper`, `Dapper.Contrib`). Cross-check the DLL `file` versions
against `packages` (from `Directory.Packages.props`).

## Stale build detection

`preflight.stale` fires when (a) any tracked `.cs/.vb/.xaml/.csproj/.props` under the repo set is
newer than the build, or (b) the app DLL's built-from SHA is behind its repo HEAD. versionize never
builds. The only real fixes are *cancel → rebuild in the IDE → re-run*, or *proceed and label the
drift*.

## Cell section content (for -new)

- **Cell AB**: what line/zones the supervisor drives, and the operator-callable features: login /
  user levels, alarm inspection, settings, page navigation (each page's purpose + features),
  device communication (which devices, which protocol/client), database / MES usage. Sources:
  `Sistec.HMI\AB`, shared `Sistec.HMI\Common`, `Sistec.UI`.
- **Cell C**: same shape for `Sistec.HMI\C`, stating what differs from AB.
- **Libraries**: each Sistec library the cells depend on + its purpose (Core, Controls, UI,
  Common, Opc.Ua, Kuka.Client/KRC, Esa.Client/Modbus, EasyModbus, Bus).

`5309AB`/`5309C` are this solution's example apps. For another target, use its own executable
projects (the script lists them under `builds`).
