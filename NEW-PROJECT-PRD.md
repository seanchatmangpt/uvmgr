# New Project Creation PRD

## Overview
The new project creation feature in uvmgr will leverage Copier templates, with [Substrate](https://github.com/superlinear-ai/substrate) as the default template. This feature will allow users to create standardized Python projects with modern tooling and best practices.

## Goals
- Provide a seamless project creation experience using Substrate as the default template
- Allow flexibility to use custom Copier templates via URL
- Ensure consistent project structure and tooling across all uvmgr-managed projects
- Automate the setup of development environments and CI/CD pipelines

## Non-Goals
- Supporting non-Copier based templates
- Creating a custom template system
- Supporting non-Python projects

## Feature Requirements

### Core Functionality

#### 1. Project Creation Command
```bash
# Basic usage with default template
uvmgr new my-project

# Using custom template
uvmgr new my-project --template https://github.com/user/custom-template

# Interactive mode with all options
uvmgr new my-project --interactive
```

#### 2. Template Management
- Default template: `gh:superlinear-ai/substrate`
- Template caching for offline use
- Template version pinning
- Template update mechanism

#### 3. Project Configuration
The system will handle these Substrate template variables:
- Project name (kebab-case)
- Package name (snake_case)
- Project description
- Author information
- License selection
- Python version
- Development tools selection:
  - Pre-commit hooks
  - Conventional commits
  - GPG signing
  - CI/CD platform (GitHub/GitLab)
  - Test coverage tools

### User Experience

#### 1. Interactive Mode
- Guided project creation with clear prompts
- Validation of user inputs
- Preview of project structure
- Summary of selected options

#### 2. Non-Interactive Mode
- Support for command-line arguments
- Environment variable overrides
- Configuration file support

#### 3. Feedback and Progress
- Clear progress indicators
- Detailed logging
- Success/failure messages
- Next steps guidance

### Technical Requirements

#### 1. Dependencies
- Copier >= 8.0.0
- uv for dependency management
- Git for template cloning
- Python 3.8+

#### 2. Project Structure
```
my-project/
├── .devcontainer/          # Dev container configuration
├── .github/               # GitHub workflows
├── src/
│   └── my_project/       # Package source
├── tests/                # Test suite
├── .pre-commit-config.yaml
├── pyproject.toml        # Project metadata and dependencies
├── README.md
└── CHANGELOG.md
```

#### 3. Development Environment
- Dev container support
- VS Code integration
- Pre-configured linting and formatting
- Git hooks setup
- Virtual environment management

### Security Considerations
- Template URL validation
- Secure template cloning
- GPG commit signing
- Dependency scanning
- License compliance checking

## Implementation Phases

### Phase 1: Core Template Integration
1. Implement basic `new` command
2. Integrate Substrate template
3. Add template URL support
4. Basic interactive mode

### Phase 2: Enhanced Features
1. Template caching
2. Advanced configuration options
3. Progress indicators
4. Validation and error handling

### Phase 3: Developer Experience
1. Dev container integration
2. VS Code settings
3. Documentation
4. Example projects

## Success Metrics
1. Project creation time < 2 minutes
2. Zero manual configuration needed for basic setup
3. 100% compatibility with Substrate template features
4. Successful CI/CD pipeline on first commit

## Future Considerations
1. Template marketplace
2. Custom template creation tools
3. Project migration tools
4. Template update management
5. Multi-language support (future)

## Documentation Requirements
1. Command-line reference
2. Template customization guide
3. Best practices
4. Troubleshooting guide
5. Migration guide from other tools

## Testing Requirements
1. Unit tests for command logic
2. Integration tests for template creation
3. End-to-end tests for full project setup
4. Template compatibility tests
5. Error handling tests

## Dependencies
- [Substrate Template](https://github.com/superlinear-ai/substrate)
- Copier
- uv
- Git
- Python 3.8+

## Timeline
- Phase 1: 2 weeks
- Phase 2: 2 weeks
- Phase 3: 2 weeks
- Documentation and Testing: 1 week

Total: 7 weeks for initial release 