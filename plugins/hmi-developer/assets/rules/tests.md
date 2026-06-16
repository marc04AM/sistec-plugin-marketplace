---
paths:
  - "**/*.Tests/**/*.cs"
  - "**/*Tests.cs"
  - "**/*Spec.cs"
---

## Testing Conventions

### Test Naming
`[MethodName]_[Scenario]_[ExpectedResult]`

```csharp
SaveAsync_WhenPlanIsNull_ReturnsFail
SaveAsync_WhenPlanHasNoLines_ReturnsFail
SaveAsync_WithValidPlan_ReturnsSuccess
OnStatusChanged_WhenStatusIsRunning_SetsIsRunningTrue
```

### Structure — Arrange / Act / Assert
```csharp
[Fact]
public async Task SaveAsync_WithValidPlan_ReturnsSuccess()
{
    // Arrange
    var db = new TestDbConnector();
    var repo = new CutPlanRepositoryAsync(db);
    var plan = new CutPlan { Lines = [new CutLine()] };

    // Act
    var result = await repo.SaveAsync(plan, db);

    // Assert
    Assert.True(result.IsSuccess);
}
```

### No Mocking of the Database
**DO NOT** use mock frameworks (`Moq`, `NSubstitute`) to replace `IDbConnector` or `IRepositoryAsync<T>`.
Use a real in-memory or test database. Mocked data layers mask schema/query failures.

### Allowed Mocks
Only mock external devices and communication layers:
- `IDevice` (OPC UA, Modbus, KUKA) — acceptable to mock; hardware not available in CI
- `ITagProvider` — mock with a `FakeTagProvider` that returns `IBasicValue<T>` stubs
- External clocks (`Func<DateTime>`) — mock for deterministic time-dependent logic

### Guard Clause Tests
Each guard clause in a method gets its own test case:
```csharp
SaveAsync_WhenPlanIsNull_ReturnsFail
SaveAsync_WhenDbIsNull_ReturnsFail
SaveAsync_WhenLinesEmpty_ReturnsFail
```

### AsyncPayload Assertions
```csharp
Assert.True(result.IsSuccess);
Assert.False(result.IsSuccess);
Assert.NotNull(result.Value);
Assert.IsType<InvalidOperationException>(result.Exception);
```

### Test Project Naming
`<ProjectName>.Tests` — one test project per WinExe project.
