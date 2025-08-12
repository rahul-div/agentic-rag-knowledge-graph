# Task Completion Workflow

## When Tasks Are Completed (from CLAUDE.md)

### Required Steps
1. **Update Tests**: After updating any logic, check whether existing unit tests need to be updated
2. **Create New Tests**: Always create Pytest unit tests for new features (functions, classes, routes)
3. **Run Linting & Type Checking**: Run lint and typecheck commands if available
4. **Mark Tasks Complete**: Mark completed tasks in `TASK.md` immediately after finishing
5. **Update Documentation**: Update `README.md` when new features, dependencies, or setup steps change

### Test Requirements
- **Test Location**: Tests should live in `/tests` folder mirroring main app structure  
- **Minimum Test Coverage**: Include at least:
  - 1 test for expected use
  - 1 edge case
  - 1 failure case
- **Test Environment**: Use venv_linux and run with `python3` commands

### Quality Assurance Checklist
- [ ] All tests pass (should be 58/58 tests)
- [ ] No type errors (if mypy available)
- [ ] Code formatted with black (if available)
- [ ] Code linted with ruff (if available)
- [ ] Documentation updated if needed
- [ ] Task marked complete in TASK.md

### Discovery During Work
- Add new sub-tasks or TODOs discovered during development to `TASK.md` under "Discovered During Work" section
- Never assume missing context - ask questions if uncertain
- Never hallucinate libraries or functions - only use known, verified Python packages
- Always confirm file paths and module names exist before referencing

### Git Workflow (when applicable)
- Never delete or overwrite existing code unless explicitly instructed
- Always prefer editing existing files over creating new ones
- Never proactively create documentation files unless requested
- Follow the principle: "Do what has been asked; nothing more, nothing less"

### Current Project Status
The project shows "✅ All core functionality completed and tested" with 58/58 tests passing, indicating it's in a production-ready state.