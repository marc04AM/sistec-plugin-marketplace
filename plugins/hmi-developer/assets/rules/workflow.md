---
paths:
  - "**/*.cs"
  - "**/*.csproj"
  - "**/*.sln"
---

## Essential Commands & Workflow

Each WinExe project has its own solution file. Run commands from the solution root via the Visual Studio Integrated Terminal.

| Task | Command |
|------|---------|
| Build | `dotnet build <ProjectName>.sln` |
| Unit Tests | `dotnet test <ProjectName>.Tests.csproj` |
| Code Formatting | `dotnet format <ProjectName>.sln` |

Examples: `dotnet build Sistec.5309AB.sln`, `dotnet build Sistec.BS.sln`

**Workflow Rule:** After modifying any file in a Communication or Business Logic layer, run `dotnet build` to verify no boundary violations were introduced.

---

## Team Guides & References
- **Diff Reviews:** Claude Code stages changes. Human engineers must use Visual Studio's Git Changes window to manually review diffs before committing.
- **Context Management:** Use `/compact` every 5-10 interactions to preserve context window limits and maintain architectural memory. Use `/clear` when switching to a completely new feature.
