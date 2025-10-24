# WORKFLOWS

Complete guide to SkillForge workflows - predefined sequences of skills that accomplish complex development tasks.

## Overview

Workflows are orchestrated sequences of skills that represent common development patterns. They provide structure, repeatability, and best practices for complex tasks.

---

## Workflow Catalog

### 1. New Project Setup
**When to use**: Starting a new project from scratch
**Duration**: 5-15 minutes
**Skills**: repository_creation, dependency_management, project_structure, documentation

### 2. Feature Development
**When to use**: Implementing new features with proper workflow
**Duration**: 30-120 minutes
**Skills**: git_branching, code_writing, testing, documentation, pull_request

### 3. Bug Fix
**When to use**: Investigating and fixing reported bugs
**Duration**: 15-60 minutes
**Skills**: debugging, code_analysis, testing, git_operations

### 4. Code Review
**When to use**: Reviewing pull requests or code changes
**Duration**: 10-30 minutes
**Skills**: code_analysis, best_practices, security_analysis, documentation_review

### 5. Deployment
**When to use**: Deploying code to production or staging
**Duration**: 10-45 minutes
**Skills**: testing, build_automation, deployment, monitoring

### 6. Refactoring
**When to use**: Improving code structure without changing behavior
**Duration**: 30-180 minutes
**Skills**: code_analysis, refactoring, testing, documentation

### 7. Documentation Update
**When to use**: Creating or updating project documentation
**Duration**: 15-45 minutes
**Skills**: documentation, code_analysis, markdown_writing

### 8. Performance Optimization
**When to use**: Improving application performance
**Duration**: 60-240 minutes
**Skills**: profiling, code_analysis, optimization, benchmarking

### 9. Security Audit
**When to use**: Checking for security vulnerabilities
**Duration**: 30-120 minutes
**Skills**: security_analysis, dependency_audit, code_analysis

### 10. Database Migration
**When to use**: Updating database schema
**Duration**: 20-60 minutes
**Skills**: database_operations, backup, migration, validation

### 11. CI/CD Setup
**When to use**: Setting up continuous integration/deployment
**Duration**: 45-120 minutes
**Skills**: automation, testing, deployment, configuration

### 12. API Development
**When to use**: Creating RESTful or GraphQL APIs
**Duration**: 60-180 minutes
**Skills**: api_design, code_writing, testing, documentation

---

## Workflow Definition Format

### YAML Schema

```yaml
workflow:
  name: string              # Required: Workflow identifier
  version: string           # Required: Semantic version
  description: string       # Required: What this workflow does
  author: string           # Optional: Creator
  tags: list[string]       # Optional: Categorization

  parameters:              # Optional: Workflow inputs
    - name: string
      type: string         # string, integer, boolean, list, dict
      required: boolean
      default: any
      description: string

  environment:             # Optional: Environment requirements
    python_version: string
    required_tools: list[string]
    env_vars: dict

  steps:                   # Required: Workflow steps
    - id: string          # Required: Step identifier
      name: string        # Required: Human-readable name
      skill: string       # Required: Skill to execute
      description: string # Optional: What this step does

      inputs:             # Optional: Step inputs
        key: value

      outputs:            # Optional: Step outputs
        - name: string
          from: string    # JSONPath to extract value

      conditions:         # Optional: When to run
        - type: string    # always, on_success, on_failure, conditional
          expression: string

      retry:              # Optional: Retry configuration
        max_attempts: integer
        delay: integer
        backoff: string   # linear, exponential

      timeout: integer    # Optional: Max execution time (seconds)

      on_error:           # Optional: Error handling
        action: string    # continue, stop, retry, rollback
        fallback_step: string

  rollback:               # Optional: Rollback procedure
    - step_id: string
      action: string

  validation:             # Optional: Final validation
    checks:
      - type: string
        target: string
        expected: any
```

### Complete Example

```yaml
workflow:
  name: feature_development
  version: "1.0.0"
  description: Complete workflow for developing a new feature
  author: SkillForge Team
  tags: [development, git, testing]

  parameters:
    - name: feature_name
      type: string
      required: true
      description: Name of the feature to develop

    - name: base_branch
      type: string
      required: false
      default: main
      description: Branch to create feature from

    - name: create_tests
      type: boolean
      required: false
      default: true
      description: Whether to create tests

  environment:
    python_version: ">=3.8"
    required_tools: [git, pytest]
    env_vars:
      SKIP_SLOW_TESTS: "false"

  steps:
    - id: create_branch
      name: Create Feature Branch
      skill: git_branching
      description: Create and checkout feature branch
      inputs:
        branch_name: "feature/{{ feature_name }}"
        base_branch: "{{ base_branch }}"
      outputs:
        - name: branch_name
          from: $.branch
      timeout: 30

    - id: implement_feature
      name: Implement Feature
      skill: code_writing
      description: Write feature implementation
      inputs:
        feature_description: "{{ feature_name }}"
        use_best_practices: true
      outputs:
        - name: files_created
          from: $.files
      conditions:
        - type: on_success
      timeout: 600

    - id: create_tests
      name: Create Tests
      skill: testing
      description: Write unit tests for feature
      inputs:
        test_type: unit
        files: "{{ steps.implement_feature.outputs.files_created }}"
      conditions:
        - type: conditional
          expression: "{{ create_tests }} == true"
      timeout: 300

    - id: run_tests
      name: Run Test Suite
      skill: testing
      description: Execute all tests
      inputs:
        coverage: true
        fail_fast: false
      retry:
        max_attempts: 2
        delay: 5
        backoff: linear
      timeout: 180

    - id: update_docs
      name: Update Documentation
      skill: documentation
      description: Document the new feature
      inputs:
        files: "{{ steps.implement_feature.outputs.files_created }}"
        format: markdown
      timeout: 120

    - id: create_pr
      name: Create Pull Request
      skill: pull_request
      description: Open PR for review
      inputs:
        title: "feat: {{ feature_name }}"
        description: "Implements {{ feature_name }}"
        labels: [feature, needs-review]
      outputs:
        - name: pr_url
          from: $.url
      timeout: 60

  rollback:
    - step_id: create_branch
      action: delete_branch
    - step_id: implement_feature
      action: revert_changes

  validation:
    checks:
      - type: file_exists
        target: "tests/test_*.py"
        expected: true
      - type: test_coverage
        target: minimum
        expected: 80
```

---

## Common Workflows

### A. New Project Setup

**Purpose**: Initialize a new project with proper structure, dependencies, and configuration.

#### Steps

1. **Project Structure Creation**
   - Skill: `project_structure`
   - Creates directories: src/, tests/, docs/, config/
   - Initializes package files: __init__.py, setup.py, pyproject.toml

2. **Git Repository Initialization**
   - Skill: `repository_creation`
   - Initializes git repo
   - Creates .gitignore
   - Makes initial commit

3. **Dependency Management**
   - Skill: `dependency_management`
   - Creates requirements.txt or pyproject.toml
   - Sets up virtual environment
   - Installs base dependencies

4. **Configuration Files**
   - Skill: `configuration`
   - Creates config.yaml, .env.example
   - Sets up linting (pylint, flake8, black)
   - Configures testing (pytest.ini, .coveragerc)

5. **Documentation Initialization**
   - Skill: `documentation`
   - Creates README.md with project overview
   - Adds CONTRIBUTING.md, LICENSE
   - Sets up docs/ structure

6. **CI/CD Setup**
   - Skill: `automation`
   - Creates .github/workflows/ or .gitlab-ci.yml
   - Configures automated testing
   - Sets up deployment pipeline

#### Example Output

```
✓ Created project structure
  - src/my_project/
  - tests/
  - docs/
  - config/

✓ Initialized git repository
  - Created .gitignore
  - Initial commit: "chore: initial project setup"

✓ Set up dependencies
  - Created pyproject.toml
  - Virtual environment: .venv/
  - Installed: pytest, black, mypy

✓ Configured development tools
  - .pylintrc
  - .flake8
  - pytest.ini

✓ Created documentation
  - README.md
  - CONTRIBUTING.md
  - LICENSE (MIT)

✓ Set up CI/CD
  - .github/workflows/test.yml
  - .github/workflows/deploy.yml

Project ready! Next steps:
  1. cd my_project
  2. source .venv/bin/activate
  3. Start coding in src/my_project/
```

#### Error Scenarios

- **Directory already exists**: Prompt for merge or abort
- **Git not installed**: Skip git initialization, warn user
- **Network error during dependency install**: Retry with exponential backoff
- **Invalid project name**: Sanitize and suggest valid name

#### YAML Definition

```yaml
workflow:
  name: new_project_setup
  version: "1.0.0"
  description: Initialize a new Python project

  parameters:
    - name: project_name
      type: string
      required: true
    - name: license
      type: string
      default: MIT
    - name: python_version
      type: string
      default: "3.11"

  steps:
    - id: create_structure
      name: Create Project Structure
      skill: project_structure
      inputs:
        name: "{{ project_name }}"
        layout: standard

    - id: init_git
      name: Initialize Git
      skill: repository_creation
      inputs:
        path: "{{ project_name }}"

    - id: setup_dependencies
      name: Setup Dependencies
      skill: dependency_management
      inputs:
        python_version: "{{ python_version }}"
        dev_dependencies: [pytest, black, mypy, flake8]

    - id: create_configs
      name: Create Configuration Files
      skill: configuration
      inputs:
        tools: [pytest, black, mypy, pylint]

    - id: init_docs
      name: Initialize Documentation
      skill: documentation
      inputs:
        license: "{{ license }}"
        include_contributing: true

    - id: setup_ci
      name: Setup CI/CD
      skill: automation
      inputs:
        platform: github_actions
        jobs: [test, lint, deploy]
```

---

### B. Feature Development

**Purpose**: Implement a new feature following best practices with proper testing and documentation.

#### Steps

1. **Branch Creation**
   - Skill: `git_branching`
   - Create feature branch from main/develop
   - Naming: feature/{feature-name}

2. **Feature Analysis**
   - Skill: `code_analysis`
   - Analyze existing codebase
   - Identify integration points
   - Plan architecture

3. **Implementation**
   - Skill: `code_writing`
   - Write feature code
   - Follow style guidelines
   - Add inline documentation

4. **Unit Testing**
   - Skill: `testing`
   - Write unit tests (>=80% coverage)
   - Test edge cases
   - Mock external dependencies

5. **Integration Testing**
   - Skill: `testing`
   - Test feature integration
   - Verify no breaking changes

6. **Documentation**
   - Skill: `documentation`
   - Update README if needed
   - Add docstrings
   - Create usage examples

7. **Code Quality Check**
   - Skill: `code_analysis`
   - Run linters
   - Check type hints
   - Verify style compliance

8. **Pull Request Creation**
   - Skill: `pull_request`
   - Create PR with description
   - Link related issues
   - Request reviewers

#### Example Output

```
Feature Development: User Authentication
========================================

✓ Created branch: feature/user-authentication

✓ Analysis complete
  - Integration points: 3
  - Existing auth system: None
  - Dependencies needed: PyJWT, bcrypt

✓ Implementation complete
  Files modified:
    - src/auth/authentication.py (new, 245 lines)
    - src/auth/models.py (new, 89 lines)
    - src/config/settings.py (modified, +12 lines)

✓ Unit tests created
  - 12 test cases
  - Coverage: 94%
  - All passing ✓

✓ Integration tests complete
  - 5 test scenarios
  - No breaking changes detected

✓ Documentation updated
  - README.md: Authentication section added
  - API documentation generated
  - Usage examples created

✓ Code quality: PASSED
  - Linting: 0 issues
  - Type checking: 0 errors
  - Complexity: within limits

✓ Pull Request created
  - URL: https://github.com/user/repo/pull/42
  - Reviewers: @tech-lead, @security-team
  - Labels: feature, security, needs-review
```

#### Skills Used
- `git_branching`: Branch management
- `code_analysis`: Code understanding
- `code_writing`: Implementation
- `testing`: Test creation and execution
- `documentation`: Documentation updates
- `pull_request`: PR creation

#### Error Scenarios

- **Merge conflicts**: Attempt auto-resolve, escalate if complex
- **Test failures**: Report failures, suggest fixes
- **Coverage below threshold**: List uncovered lines
- **Linting errors**: Auto-fix if possible, report non-fixable

---

### C. Bug Fix

**Purpose**: Investigate, fix, and verify bug resolution with proper testing.

#### Steps

1. **Bug Reproduction**
   - Skill: `debugging`
   - Reproduce the bug
   - Document reproduction steps
   - Capture error messages/stack traces

2. **Root Cause Analysis**
   - Skill: `code_analysis`
   - Trace execution path
   - Identify faulty code
   - Understand why it fails

3. **Create Bug Fix Branch**
   - Skill: `git_branching`
   - Branch naming: fix/{bug-description}
   - Track issue number

4. **Implement Fix**
   - Skill: `code_writing`
   - Minimal change approach
   - Add defensive code if needed
   - Update error handling

5. **Create Regression Test**
   - Skill: `testing`
   - Write test that fails without fix
   - Verify test passes with fix
   - Cover related edge cases

6. **Verify Fix**
   - Skill: `testing`
   - Run full test suite
   - Manual testing if needed
   - Check for side effects

7. **Update Documentation**
   - Skill: `documentation`
   - Update changelog
   - Add code comments
   - Document known limitations

8. **Create Fix PR**
   - Skill: `pull_request`
   - Reference issue number
   - Explain root cause and fix
   - Tag for backporting if needed

#### Example Output

```
Bug Fix: Division by Zero in Calculation Module
===============================================

✓ Bug reproduced
  Steps:
    1. Call calculate_average([])
    2. Observe ZeroDivisionError

  Error: ZeroDivisionError: division by zero
    at src/utils/math.py:45

✓ Root cause identified
  Location: src/utils/math.py:45
  Issue: No check for empty list before sum/len
  Impact: High - crashes application

✓ Created branch: fix/division-by-zero-in-average

✓ Fix implemented
  File: src/utils/math.py
  Changes:
    - Added empty list check
    - Return 0 for empty list (documented behavior)
    - Added type hints

✓ Regression test created
  File: tests/utils/test_math.py
  New tests:
    - test_calculate_average_empty_list
    - test_calculate_average_single_item
    - test_calculate_average_negative_numbers

✓ Fix verified
  - Regression test: PASS
  - Full test suite: 127/127 PASS
  - Manual testing: Verified

✓ Documentation updated
  - CHANGELOG.md: Added fix entry
  - Docstring: Documented empty list behavior

✓ Pull Request created
  - URL: https://github.com/user/repo/pull/43
  - Closes: #156
  - Labels: bug, high-priority
  - Recommended for backport to v1.2.x
```

#### Skills Used
- `debugging`: Bug investigation
- `code_analysis`: Root cause analysis
- `git_branching`: Branch creation
- `code_writing`: Fix implementation
- `testing`: Test creation and verification
- `documentation`: Change documentation
- `pull_request`: PR creation

---

### D. Code Review

**Purpose**: Systematically review code changes for quality, security, and best practices.

#### Steps

1. **Fetch Changes**
   - Skill: `git_operations`
   - Fetch PR branch
   - Identify changed files
   - Generate diff summary

2. **Architecture Review**
   - Skill: `code_analysis`
   - Assess design patterns
   - Check separation of concerns
   - Verify scalability considerations

3. **Code Quality Analysis**
   - Skill: `best_practices`
   - Check naming conventions
   - Verify code complexity
   - Assess readability
   - Check for code duplication

4. **Security Analysis**
   - Skill: `security_analysis`
   - Check for SQL injection
   - Verify input validation
   - Check authentication/authorization
   - Scan for hardcoded secrets

5. **Test Review**
   - Skill: `testing`
   - Verify test coverage
   - Check test quality
   - Ensure edge cases covered

6. **Documentation Review**
   - Skill: `documentation_review`
   - Check docstrings
   - Verify README updates
   - Assess code comments

7. **Performance Check**
   - Skill: `profiling`
   - Identify potential bottlenecks
   - Check algorithm complexity
   - Verify resource usage

8. **Generate Feedback**
   - Skill: `documentation`
   - Create structured feedback
   - Prioritize issues
   - Suggest improvements

#### Review Checklist

```markdown
## Architecture & Design
- [ ] Follows project architecture patterns
- [ ] Appropriate separation of concerns
- [ ] No circular dependencies
- [ ] Scalable design

## Code Quality
- [ ] Clear, descriptive naming
- [ ] Functions are focused and small
- [ ] No code duplication
- [ ] Appropriate error handling
- [ ] Type hints present

## Security
- [ ] Input validation present
- [ ] No SQL injection vulnerabilities
- [ ] No hardcoded credentials
- [ ] Proper authentication/authorization
- [ ] Sensitive data encrypted

## Testing
- [ ] Unit tests present
- [ ] Coverage >= 80%
- [ ] Edge cases tested
- [ ] Tests are maintainable

## Documentation
- [ ] Docstrings for public APIs
- [ ] README updated if needed
- [ ] Complex logic explained
- [ ] API changes documented

## Performance
- [ ] No obvious bottlenecks
- [ ] Efficient algorithms
- [ ] Appropriate data structures
- [ ] Resource cleanup handled
```

#### Example Output

```
Code Review: Feature/User-Authentication (PR #42)
=================================================

Overview:
  Files changed: 8
  Lines added: 456
  Lines removed: 23
  Complexity: Medium

✓ Architecture Review
  Score: 8/10

  Strengths:
    - Clean separation of concerns
    - Follows MVC pattern
    - Good use of dependency injection

  Suggestions:
    - Consider extracting auth logic to separate service layer

✓ Code Quality
  Score: 9/10

  Strengths:
    - Excellent naming conventions
    - Well-structured functions
    - Good use of type hints

  Issues:
    ⚠️ Minor: Function authenticate_user() is 45 lines (recommend <30)
    💡 Suggestion: Extract validation logic to separate function

✓ Security Analysis
  Score: 7/10

  ⚠️ Important Issues Found:
    1. Password hashing uses MD5 (INSECURE)
       Location: src/auth/authentication.py:67
       Fix: Use bcrypt or argon2

    2. JWT secret loaded from code
       Location: src/config/settings.py:12
       Fix: Move to environment variable

  ✓ Strengths:
    - Input validation present
    - No SQL injection risks
    - Rate limiting implemented

✓ Test Review
  Score: 9/10

  Coverage: 94% (target: 80%)
  Tests: 17 total, all passing

  ✓ Strengths:
    - Comprehensive edge case testing
    - Good use of mocks
    - Clear test names

  💡 Suggestion: Add integration test for token refresh flow

✓ Documentation
  Score: 8/10

  ✓ Strengths:
    - All public functions documented
    - README updated with auth examples
    - API endpoints documented

  ⚠️ Minor: Missing docstring for _validate_token_expiry()

✓ Performance
  Score: 8/10

  No major concerns

  💡 Optimization opportunities:
    - Cache user lookup results (15ms saved per request)
    - Consider async for token validation

Summary:
--------
Overall Score: 8.2/10

Decision: REQUEST CHANGES

Critical Issues: 1 (security)
Important Issues: 1 (security)
Minor Issues: 2
Suggestions: 4

Action Items:
1. 🔴 MUST FIX: Replace MD5 with bcrypt for password hashing
2. 🟡 SHOULD FIX: Move JWT secret to environment variable
3. 💡 NICE TO HAVE: Refactor authenticate_user() function
4. 💡 NICE TO HAVE: Add integration test for token refresh

Once security issues are resolved, this will be ready to merge!
```

#### Skills Used
- `git_operations`: Fetch and analyze changes
- `code_analysis`: Architecture and quality review
- `security_analysis`: Security scanning
- `best_practices`: Standards verification
- `testing`: Test coverage analysis
- `documentation_review`: Documentation check
- `profiling`: Performance analysis

---

### E. Deployment

**Purpose**: Deploy code to production with pre/post-deployment validation.

#### Steps

1. **Pre-Deployment Checks**
   - Skill: `validation`
   - Verify all tests pass
   - Check code coverage
   - Validate configuration
   - Ensure migrations ready

2. **Database Backup**
   - Skill: `backup`
   - Create database snapshot
   - Verify backup integrity
   - Document restore procedure

3. **Build Application**
   - Skill: `build_automation`
   - Run build process
   - Generate artifacts
   - Verify build success

4. **Run Database Migrations**
   - Skill: `database_operations`
   - Apply pending migrations
   - Verify schema changes
   - Update migration history

5. **Deploy Application**
   - Skill: `deployment`
   - Deploy to target environment
   - Update configuration
   - Restart services

6. **Smoke Tests**
   - Skill: `testing`
   - Verify critical paths
   - Check health endpoints
   - Test key features

7. **Monitor Deployment**
   - Skill: `monitoring`
   - Watch error rates
   - Monitor performance metrics
   - Check logs for issues

8. **Post-Deployment Validation**
   - Skill: `validation`
   - Verify all services running
   - Check external integrations
   - Validate data integrity

#### Example Output

```
Deployment: Production v2.3.0
=============================

✓ Pre-deployment checks
  - Tests: 234/234 PASS
  - Coverage: 87%
  - Config validation: PASS
  - Migrations: 3 pending

✓ Database backup created
  - Snapshot: prod-db-2024-01-15-14-30
  - Size: 2.4 GB
  - Verification: PASS
  - Location: s3://backups/prod/

✓ Build complete
  - Build #456
  - Artifact: app-v2.3.0.tar.gz
  - Size: 45 MB
  - Checksum: a8f3e7c...

✓ Database migrations applied
  - 001_add_user_preferences.sql: SUCCESS
  - 002_update_indexes.sql: SUCCESS
  - 003_add_audit_tables.sql: SUCCESS
  - Duration: 12s

✓ Application deployed
  - Target: prod-cluster-1
  - Instances: 6/6 updated
  - Strategy: rolling update
  - Duration: 3m 45s

✓ Smoke tests PASSED
  - Health endpoint: ✓
  - User login: ✓
  - API endpoints: ✓
  - Database connectivity: ✓

✓ Monitoring: All clear
  - Error rate: 0.02% (baseline: 0.03%)
  - Response time: 145ms avg (baseline: 150ms)
  - CPU usage: 34% (normal)
  - Memory usage: 62% (normal)

✓ Post-deployment validation
  - All services: HEALTHY
  - External APIs: CONNECTED
  - Data integrity: VERIFIED

Deployment successful! 🚀
  Version: v2.3.0
  Deployed at: 2024-01-15 14:45:23 UTC
  Rollback available: yes
```

#### Skills Used
- `validation`: Pre/post-deployment checks
- `backup`: Database backup
- `build_automation`: Build process
- `database_operations`: Migration management
- `deployment`: Deployment execution
- `testing`: Smoke testing
- `monitoring`: Metrics monitoring

#### Error Scenarios

- **Test failures**: Abort deployment
- **Backup failure**: Retry, then abort if still fails
- **Migration failure**: Rollback migration, abort deployment
- **Deployment failure**: Rollback to previous version
- **Smoke test failure**: Investigate, rollback if critical

---

### F. Refactoring

**Purpose**: Improve code structure and maintainability without changing behavior.

#### Steps

1. **Code Analysis**
   - Skill: `code_analysis`
   - Identify code smells
   - Calculate complexity metrics
   - Find duplication

2. **Generate Refactoring Plan**
   - Skill: `refactoring`
   - Prioritize refactoring targets
   - Estimate effort
   - Identify risks

3. **Baseline Tests**
   - Skill: `testing`
   - Ensure tests exist
   - Run test suite (baseline)
   - Add missing tests

4. **Incremental Refactoring**
   - Skill: `refactoring`
   - Apply one refactoring at a time
   - Run tests after each change
   - Commit incrementally

5. **Performance Validation**
   - Skill: `benchmarking`
   - Compare before/after performance
   - Ensure no regression

6. **Documentation Update**
   - Skill: `documentation`
   - Update architecture docs
   - Revise code comments
   - Document design decisions

7. **Final Validation**
   - Skill: `testing`
   - Full test suite
   - Code quality checks
   - Performance benchmarks

#### Refactoring Patterns

```python
# Common refactoring operations:

# 1. Extract Method
# 2. Extract Class
# 3. Rename Variable/Method/Class
# 4. Move Method/Field
# 5. Replace Conditional with Polymorphism
# 6. Introduce Parameter Object
# 7. Replace Magic Number with Constant
# 8. Decompose Conditional
# 9. Consolidate Duplicate Conditional Fragments
# 10. Replace Nested Conditional with Guard Clauses
```

#### Example Output

```
Refactoring: User Management Module
====================================

✓ Analysis complete
  Files analyzed: 12
  Lines of code: 2,456

  Issues found:
    - High complexity: 5 functions
    - Code duplication: 8 instances (234 lines)
    - Long methods: 7 (>50 lines)
    - Large classes: 2 (>300 lines)

✓ Refactoring plan generated
  Priority 1: Extract UserValidator class (high complexity)
  Priority 2: Consolidate duplicate validation logic
  Priority 3: Split UserManager class (too large)
  Priority 4: Extract email notification logic

  Estimated effort: 4-6 hours
  Risk level: Low (good test coverage)

✓ Baseline tests
  Tests: 89/89 PASS
  Coverage: 91%
  Performance baseline captured

✓ Refactoring step 1: Extract UserValidator
  - Created validators/user_validator.py
  - Moved validation logic
  - Updated imports
  - Tests: 89/89 PASS ✓

✓ Refactoring step 2: Consolidate duplicates
  - Removed 234 lines of duplication
  - Created shared validation functions
  - Updated all call sites
  - Tests: 89/89 PASS ✓

✓ Refactoring step 3: Split UserManager
  - Created UserCreationService
  - Created UserUpdateService
  - Delegated from UserManager
  - Tests: 89/89 PASS ✓

✓ Refactoring step 4: Extract notifications
  - Created notifications/user_notifier.py
  - Moved email logic
  - Added dependency injection
  - Tests: 89/89 PASS ✓

✓ Performance validation
  Before:
    - user_creation: 45ms avg
    - user_update: 32ms avg

  After:
    - user_creation: 43ms avg (-4%)
    - user_update: 31ms avg (-3%)

  Result: No performance regression ✓

✓ Documentation updated
  - Updated architecture.md
  - Added class diagrams
  - Documented design decisions

✓ Final validation
  - Tests: 89/89 PASS
  - Coverage: 92% (+1%)
  - Complexity: Reduced by 35%
  - Code quality score: 8.9/10 (was 7.2)

Refactoring complete!
  Lines removed: 312
  Lines added: 189
  Net reduction: 123 lines (-5%)
  Complexity reduction: 35%
  Maintainability: Significantly improved
```

#### Skills Used
- `code_analysis`: Issue identification
- `refactoring`: Code transformation
- `testing`: Validation
- `benchmarking`: Performance comparison
- `documentation`: Documentation updates

---

### G. Documentation Update

**Purpose**: Create or update project documentation comprehensively.

#### Steps

1. **Documentation Audit**
   - Skill: `documentation_review`
   - Identify missing docs
   - Find outdated content
   - Check for broken links

2. **Code Analysis for Docs**
   - Skill: `code_analysis`
   - Extract public APIs
   - Identify undocumented features
   - Generate API signatures

3. **Generate API Documentation**
   - Skill: `documentation`
   - Create API reference
   - Add usage examples
   - Document parameters/returns

4. **Update User Guides**
   - Skill: `documentation`
   - Update README
   - Create tutorials
   - Add troubleshooting section

5. **Generate Code Examples**
   - Skill: `code_writing`
   - Write example code
   - Ensure examples work
   - Cover common use cases

6. **Create Architecture Docs**
   - Skill: `documentation`
   - Document system design
   - Add diagrams
   - Explain key decisions

7. **Validation**
   - Skill: `testing`
   - Test code examples
   - Check links
   - Verify accuracy

#### Documentation Structure

```
docs/
├── README.md                 # Project overview
├── GETTING_STARTED.md       # Quick start guide
├── INSTALLATION.md          # Installation instructions
├── CONFIGURATION.md         # Configuration guide
├── API_REFERENCE.md         # API documentation
├── TUTORIALS.md             # Step-by-step tutorials
├── ARCHITECTURE.md          # System architecture
├── CONTRIBUTING.md          # Contribution guidelines
├── CHANGELOG.md             # Version history
├── TROUBLESHOOTING.md       # Common issues
└── examples/                # Code examples
    ├── basic_usage.py
    ├── advanced_features.py
    └── integration_example.py
```

#### Example Output

```
Documentation Update
====================

✓ Documentation audit
  Files checked: 15
  Issues found:
    - Missing: API_REFERENCE.md
    - Outdated: INSTALLATION.md (6 months old)
    - Broken links: 3
    - Missing examples: 8 features

✓ Code analysis
  Public APIs discovered: 47
  Undocumented: 12
  Missing docstrings: 5

✓ API documentation generated
  Created: docs/API_REFERENCE.md
  Sections:
    - Core Classes (12)
    - Utility Functions (18)
    - Configuration Options (17)

  Examples added: 47
  Coverage: 100%

✓ User guides updated
  Updated: README.md
    - Added feature matrix
    - Updated installation steps
    - Added badges and shields

  Updated: GETTING_STARTED.md
    - Refreshed quick start
    - Added 5-minute tutorial
    - Updated screenshots

  Created: TROUBLESHOOTING.md
    - Common errors: 15
    - Solutions provided
    - Debug tips included

✓ Code examples created
  examples/basic_usage.py: ✓
  examples/advanced_features.py: ✓
  examples/async_operations.py: ✓
  examples/plugin_system.py: ✓
  examples/cli_interface.py: ✓

✓ Architecture documentation
  Created: docs/ARCHITECTURE.md
    - System overview
    - Component diagram
    - Data flow diagram
    - Design decisions

✓ Validation complete
  - All examples tested: PASS
  - Links checked: 0 broken
  - Spelling: 0 errors
  - Accuracy verified

Documentation complete!
  Files created: 4
  Files updated: 6
  Examples added: 5
  Total pages: ~45
```

#### Skills Used
- `documentation_review`: Audit existing docs
- `code_analysis`: API discovery
- `documentation`: Doc generation
- `code_writing`: Example creation
- `testing`: Example validation

---

### H. Performance Optimization

**Purpose**: Identify and resolve performance bottlenecks.

#### Steps

1. **Baseline Profiling**
   - Skill: `profiling`
   - Profile application
   - Measure key metrics
   - Identify bottlenecks

2. **Analysis**
   - Skill: `code_analysis`
   - Analyze hot paths
   - Review algorithms
   - Check database queries

3. **Optimization Planning**
   - Skill: `optimization`
   - Prioritize optimizations
   - Estimate impact
   - Assess risk

4. **Implement Optimizations**
   - Skill: `optimization`
   - Apply optimizations
   - One change at a time
   - Benchmark each change

5. **Database Optimization**
   - Skill: `database_operations`
   - Add indexes
   - Optimize queries
   - Implement caching

6. **Caching Strategy**
   - Skill: `optimization`
   - Identify cacheable data
   - Implement caching layer
   - Set cache policies

7. **Load Testing**
   - Skill: `testing`
   - Run load tests
   - Measure improvements
   - Identify new bottlenecks

8. **Final Benchmarking**
   - Skill: `benchmarking`
   - Compare before/after
   - Document improvements
   - Update performance docs

#### Example Output

```
Performance Optimization
========================

✓ Baseline profiling
  Tool: cProfile + memory_profiler
  Scenario: 1000 concurrent users

  Metrics:
    - Response time: 850ms avg
    - Throughput: 45 req/s
    - Memory: 2.1 GB
    - CPU: 78% avg

  Bottlenecks identified:
    1. Database queries: 65% of time
    2. JSON serialization: 18% of time
    3. Regex operations: 12% of time

✓ Analysis complete
  Hot path: user_list_view()
    - 45 database queries (N+1 problem)
    - Missing indexes on user.created_at
    - Inefficient JSON encoder
    - Regex compiled on every request

✓ Optimization plan
  Priority 1: Fix N+1 queries (expected: -60% time)
  Priority 2: Add database indexes (expected: -15% time)
  Priority 3: Optimize JSON encoding (expected: -10% time)
  Priority 4: Cache compiled regex (expected: -5% time)

✓ Optimization 1: Fix N+1 queries
  Changes:
    - Added select_related() calls
    - Implemented prefetch_related()
    - Reduced queries from 45 to 3

  Benchmark:
    - Response time: 425ms (-50%)
    - Database time: 180ms (was 550ms)

✓ Optimization 2: Database indexes
  Indexes added:
    - user.created_at
    - user.email (covering index)
    - user_profile.user_id

  Benchmark:
    - Response time: 320ms (-25%)
    - Query time: 85ms (was 180ms)

✓ Optimization 3: JSON optimization
  Changes:
    - Switched to orjson
    - Implemented custom encoder
    - Reduced serialization overhead

  Benchmark:
    - Response time: 280ms (-12%)
    - Serialization: 25ms (was 153ms)

✓ Optimization 4: Cache regex
  Changes:
    - Compile regex at module level
    - Cache patterns dict

  Benchmark:
    - Response time: 265ms (-5%)
    - Regex time: 8ms (was 102ms)

✓ Caching strategy
  Implemented:
    - Redis cache for user data (5min TTL)
    - Query result caching
    - Template fragment caching

  Cache hit rate: 67%
  Response time with cache: 45ms

✓ Load testing
  Tool: locust
  Scenario: 1000 concurrent users, 5 minutes

  Results:
    - Response time: 52ms avg (was 850ms)
    - 95th percentile: 125ms (was 2.1s)
    - Throughput: 580 req/s (was 45)
    - Error rate: 0% (was 0%)
    - Memory: 1.4 GB (was 2.1 GB)

✓ Final benchmarks

  Performance Improvements:
  ┌─────────────────────┬──────────┬─────────┬─────────────┐
  │ Metric              │ Before   │ After   │ Improvement │
  ├─────────────────────┼──────────┼─────────┼─────────────┤
  │ Response Time       │ 850ms    │ 52ms    │ 94% faster  │
  │ Throughput          │ 45/s     │ 580/s   │ 12.9x       │
  │ Memory Usage        │ 2.1 GB   │ 1.4 GB  │ 33% less    │
  │ CPU Usage           │ 78%      │ 34%     │ 56% less    │
  │ Database Queries    │ 45       │ 3       │ 93% fewer   │
  └─────────────────────┴──────────┴─────────┴─────────────┘

Optimization complete! 🚀
  Overall improvement: 94% faster
  ROI: Excellent
  No functionality changes
```

#### Skills Used
- `profiling`: Performance measurement
- `code_analysis`: Bottleneck identification
- `optimization`: Performance improvements
- `database_operations`: Database tuning
- `testing`: Load testing
- `benchmarking`: Performance comparison

---

## Workflow Orchestration

### Workflow Engine

```python
"""
SkillForge Workflow Orchestration Engine
Executes workflows with dependency management, error handling, and state tracking.
"""

import yaml
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re


class StepStatus(Enum):
    """Step execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class ConditionType(Enum):
    """Step condition types"""
    ALWAYS = "always"
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"
    CONDITIONAL = "conditional"


@dataclass
class StepResult:
    """Result of a step execution"""
    step_id: str
    status: StepStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowState:
    """Current state of workflow execution"""
    workflow_id: str
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    status: str = "running"
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class WorkflowOrchestrator:
    """
    Orchestrates workflow execution with:
    - Dependency management
    - Parallel execution
    - Error recovery
    - State management
    - Variable interpolation
    """

    def __init__(self, skill_executor=None):
        self.logger = logging.getLogger(__name__)
        self.skill_executor = skill_executor or SkillExecutor()
        self.state: Optional[WorkflowState] = None

    def load_workflow(self, workflow_path: str) -> Dict[str, Any]:
        """Load workflow definition from YAML file"""
        with open(workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)

        self._validate_workflow(workflow)
        return workflow

    def execute(
        self,
        workflow: Dict[str, Any],
        parameters: Dict[str, Any] = None
    ) -> WorkflowState:
        """
        Execute workflow with given parameters

        Args:
            workflow: Workflow definition
            parameters: Runtime parameters

        Returns:
            WorkflowState with execution results
        """
        workflow_id = workflow['workflow']['name']
        self.state = WorkflowState(workflow_id=workflow_id)

        # Merge parameters with defaults
        params = self._merge_parameters(workflow, parameters or {})
        self.state.variables.update(params)

        try:
            # Execute workflow steps
            steps = workflow['workflow']['steps']

            for step in steps:
                # Check if step should be executed
                if not self._should_execute_step(step):
                    self._skip_step(step)
                    continue

                # Execute step
                result = self._execute_step(step)

                # Update state
                self.state.step_results[step['id']] = result

                if result.status == StepStatus.SUCCESS:
                    self.state.completed_steps.append(step['id'])
                    # Store step outputs in variables
                    if result.outputs:
                        self._process_step_outputs(step, result)
                elif result.status == StepStatus.FAILED:
                    self.state.failed_steps.append(step['id'])
                    self._handle_step_failure(step, result)

            # Validate workflow completion
            if 'validation' in workflow['workflow']:
                self._validate_workflow_results(workflow['workflow']['validation'])

            self.state.status = "completed"

        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            self.state.status = "failed"
            # Attempt rollback if defined
            if 'rollback' in workflow['workflow']:
                self._rollback(workflow['workflow']['rollback'])

        finally:
            self.state.completed_at = datetime.now()

        return self.state

    def _execute_step(self, step: Dict[str, Any]) -> StepResult:
        """Execute a single workflow step"""
        step_id = step['id']
        skill = step['skill']

        self.logger.info(f"Executing step: {step_id} ({skill})")
        self.state.current_step = step_id

        start_time = datetime.now()

        try:
            # Interpolate inputs
            inputs = self._interpolate_variables(step.get('inputs', {}))

            # Execute skill with retry logic
            max_attempts = 1
            if 'retry' in step:
                max_attempts = step['retry']['max_attempts']

            last_error = None
            for attempt in range(max_attempts):
                try:
                    outputs = self.skill_executor.execute(skill, inputs)

                    duration = (datetime.now() - start_time).total_seconds()
                    return StepResult(
                        step_id=step_id,
                        status=StepStatus.SUCCESS,
                        outputs=outputs,
                        duration=duration
                    )

                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        delay = step['retry'].get('delay', 1)
                        if step['retry'].get('backoff') == 'exponential':
                            delay *= (2 ** attempt)
                        self.logger.warning(
                            f"Step {step_id} failed (attempt {attempt + 1}), "
                            f"retrying in {delay}s"
                        )
                        import time
                        time.sleep(delay)

            # All attempts failed
            raise last_error

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Step {step_id} failed: {e}")
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error=str(e),
                duration=duration
            )

    def _should_execute_step(self, step: Dict[str, Any]) -> bool:
        """Determine if step should be executed based on conditions"""
        if 'conditions' not in step:
            return True

        for condition in step['conditions']:
            cond_type = ConditionType(condition['type'])

            if cond_type == ConditionType.ALWAYS:
                return True

            elif cond_type == ConditionType.ON_SUCCESS:
                # Check if all previous steps succeeded
                if self.state.failed_steps:
                    return False

            elif cond_type == ConditionType.ON_FAILURE:
                # Only run if previous step failed
                if not self.state.failed_steps:
                    return False

            elif cond_type == ConditionType.CONDITIONAL:
                # Evaluate expression
                expression = condition['expression']
                result = self._evaluate_expression(expression)
                if not result:
                    return False

        return True

    def _handle_step_failure(self, step: Dict[str, Any], result: StepResult):
        """Handle step failure according to on_error configuration"""
        if 'on_error' not in step:
            raise Exception(f"Step {step['id']} failed: {result.error}")

        on_error = step['on_error']
        action = on_error['action']

        if action == 'continue':
            self.logger.warning(f"Step {step['id']} failed but continuing")

        elif action == 'stop':
            raise Exception(f"Step {step['id']} failed: {result.error}")

        elif action == 'retry':
            # Retry already handled in _execute_step
            raise Exception(f"Step {step['id']} failed after retries: {result.error}")

        elif action == 'rollback':
            raise Exception(f"Step {step['id']} failed, triggering rollback")

        elif action == 'fallback' and 'fallback_step' in on_error:
            self.logger.info(f"Executing fallback step: {on_error['fallback_step']}")
            # Execute fallback step
            # Implementation depends on workflow structure

    def _interpolate_variables(self, data: Any) -> Any:
        """
        Interpolate variables in data using {{ variable }} syntax
        Supports:
        - Simple variables: {{ var_name }}
        - Nested access: {{ steps.step1.outputs.result }}
        - Parameters: {{ parameters.param_name }}
        """
        if isinstance(data, str):
            # Find all {{ ... }} patterns
            pattern = r'\{\{\s*([^}]+)\s*\}\}'

            def replace(match):
                expr = match.group(1).strip()
                value = self._resolve_variable(expr)
                return str(value) if value is not None else match.group(0)

            return re.sub(pattern, replace, data)

        elif isinstance(data, dict):
            return {k: self._interpolate_variables(v) for k, v in data.items()}

        elif isinstance(data, list):
            return [self._interpolate_variables(item) for item in data]

        return data

    def _resolve_variable(self, expr: str) -> Any:
        """Resolve variable expression to value"""
        parts = expr.split('.')

        # Start with state variables
        value = self.state.variables

        # Special prefixes
        if parts[0] == 'steps':
            # Access step results: steps.step_id.outputs.key
            step_id = parts[1]
            if step_id in self.state.step_results:
                value = self.state.step_results[step_id]
                parts = parts[2:]  # Skip 'steps' and step_id

        # Navigate through nested structure
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

        return value

    def _evaluate_expression(self, expression: str) -> bool:
        """Evaluate conditional expression"""
        # Interpolate variables first
        expr = self._interpolate_variables(expression)

        # Safe evaluation (simple comparisons only)
        try:
            # This is a simplified evaluator
            # In production, use a proper expression parser
            return eval(expr, {"__builtins__": {}}, {})
        except Exception as e:
            self.logger.error(f"Failed to evaluate expression '{expr}': {e}")
            return False

    def _process_step_outputs(self, step: Dict[str, Any], result: StepResult):
        """Process step outputs and store in state variables"""
        if 'outputs' not in step:
            return

        for output_def in step['outputs']:
            name = output_def['name']
            from_path = output_def.get('from', f'$.{name}')

            # Extract value using JSONPath-like syntax
            value = self._extract_from_jsonpath(result.outputs, from_path)

            # Store in variables
            if 'steps' not in self.state.variables:
                self.state.variables['steps'] = {}

            if step['id'] not in self.state.variables['steps']:
                self.state.variables['steps'][step['id']] = {'outputs': {}}

            self.state.variables['steps'][step['id']]['outputs'][name] = value

    def _extract_from_jsonpath(self, data: Dict, path: str) -> Any:
        """Extract value using simplified JSONPath"""
        # Remove leading $
        if path.startswith('$.'):
            path = path[2:]

        parts = path.split('.')
        value = data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def _skip_step(self, step: Dict[str, Any]):
        """Mark step as skipped"""
        result = StepResult(
            step_id=step['id'],
            status=StepStatus.SKIPPED
        )
        self.state.step_results[step['id']] = result
        self.logger.info(f"Skipped step: {step['id']}")

    def _validate_workflow_results(self, validation: Dict[str, Any]):
        """Validate workflow results against defined checks"""
        checks = validation.get('checks', [])

        for check in checks:
            check_type = check['type']
            target = check['target']
            expected = check['expected']

            # Implement different validation types
            if check_type == 'file_exists':
                # Check if file exists
                import os
                pattern = self._interpolate_variables(target)
                # Use glob to check pattern
                import glob
                matches = glob.glob(pattern)
                if not matches and expected:
                    raise Exception(f"Validation failed: No files match {pattern}")

            elif check_type == 'test_coverage':
                # Check test coverage
                coverage_key = f'coverage_{target}'
                if coverage_key in self.state.variables:
                    actual = self.state.variables[coverage_key]
                    if actual < expected:
                        raise Exception(
                            f"Validation failed: Coverage {actual}% < {expected}%"
                        )

    def _rollback(self, rollback_config: List[Dict[str, Any]]):
        """Execute rollback procedures"""
        self.logger.warning("Executing rollback procedures")

        for rollback_step in reversed(rollback_config):
            step_id = rollback_step['step_id']
            action = rollback_step['action']

            if step_id not in self.state.completed_steps:
                continue

            try:
                self.logger.info(f"Rolling back {step_id}: {action}")
                # Execute rollback action
                # This would call specific rollback skills
                self.skill_executor.execute(f"rollback_{action}", {
                    'step_id': step_id,
                    'state': self.state.variables
                })

                # Mark as rolled back
                if step_id in self.state.step_results:
                    self.state.step_results[step_id].status = StepStatus.ROLLED_BACK

            except Exception as e:
                self.logger.error(f"Rollback failed for {step_id}: {e}")

    def _merge_parameters(
        self,
        workflow: Dict[str, Any],
        provided: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge provided parameters with defaults"""
        if 'parameters' not in workflow['workflow']:
            return provided

        params = {}

        for param_def in workflow['workflow']['parameters']:
            name = param_def['name']

            if name in provided:
                params[name] = provided[name]
            elif 'default' in param_def:
                params[name] = param_def['default']
            elif param_def.get('required', False):
                raise ValueError(f"Required parameter '{name}' not provided")

        return params

    def _validate_workflow(self, workflow: Dict[str, Any]):
        """Validate workflow definition"""
        if 'workflow' not in workflow:
            raise ValueError("Invalid workflow: missing 'workflow' key")

        wf = workflow['workflow']

        required = ['name', 'version', 'steps']
        for field in required:
            if field not in wf:
                raise ValueError(f"Invalid workflow: missing '{field}'")

        # Validate steps
        for step in wf['steps']:
            if 'id' not in step or 'skill' not in step:
                raise ValueError("Invalid step: missing 'id' or 'skill'")

    def save_state(self, filepath: str):
        """Save workflow state to file for resumption"""
        state_dict = {
            'workflow_id': self.state.workflow_id,
            'current_step': self.state.current_step,
            'completed_steps': self.state.completed_steps,
            'failed_steps': self.state.failed_steps,
            'variables': self.state.variables,
            'status': self.state.status,
            'started_at': self.state.started_at.isoformat(),
            'step_results': {
                step_id: {
                    'status': result.status.value,
                    'outputs': result.outputs,
                    'error': result.error,
                    'duration': result.duration
                }
                for step_id, result in self.state.step_results.items()
            }
        }

        with open(filepath, 'w') as f:
            json.dump(state_dict, f, indent=2)

    def load_state(self, filepath: str) -> WorkflowState:
        """Load workflow state from file"""
        with open(filepath, 'r') as f:
            state_dict = json.load(f)

        # Reconstruct state
        self.state = WorkflowState(
            workflow_id=state_dict['workflow_id'],
            current_step=state_dict['current_step'],
            completed_steps=state_dict['completed_steps'],
            failed_steps=state_dict['failed_steps'],
            variables=state_dict['variables'],
            status=state_dict['status'],
            started_at=datetime.fromisoformat(state_dict['started_at'])
        )

        # Reconstruct step results
        for step_id, result_dict in state_dict['step_results'].items():
            self.state.step_results[step_id] = StepResult(
                step_id=step_id,
                status=StepStatus(result_dict['status']),
                outputs=result_dict['outputs'],
                error=result_dict['error'],
                duration=result_dict['duration']
            )

        return self.state


class SkillExecutor:
    """Mock skill executor for demonstration"""

    def execute(self, skill: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a skill with given inputs"""
        # This would integrate with actual SkillForge skill execution
        print(f"Executing skill: {skill}")
        print(f"Inputs: {inputs}")

        # Return mock outputs
        return {
            'success': True,
            'result': f"Executed {skill}"
        }


# Example usage
if __name__ == "__main__":
    orchestrator = WorkflowOrchestrator()

    # Load workflow
    workflow = orchestrator.load_workflow('workflows/feature_development.yaml')

    # Execute with parameters
    state = orchestrator.execute(workflow, {
        'feature_name': 'user-authentication',
        'base_branch': 'develop',
        'create_tests': True
    })

    # Save state for resumption
    orchestrator.save_state('workflow_state.json')

    print(f"Workflow {state.workflow_id}: {state.status}")
    print(f"Completed steps: {len(state.completed_steps)}")
    print(f"Failed steps: {len(state.failed_steps)}")
```

---

## Custom Workflows

### Creating Custom Workflows

Users can create custom workflows by defining YAML files following the workflow schema.

#### Template Structure

```yaml
workflow:
  name: my_custom_workflow
  version: "1.0.0"
  description: Description of what this workflow does

  parameters:
    - name: param1
      type: string
      required: true
      description: Description of parameter

  steps:
    - id: step1
      name: Step 1 Name
      skill: skill_name
      inputs:
        key: "{{ param1 }}"
      outputs:
        - name: result
          from: $.output_key

    - id: step2
      name: Step 2 Name
      skill: another_skill
      inputs:
        data: "{{ steps.step1.outputs.result }}"
      conditions:
        - type: on_success
```

#### Variables and Interpolation

Variables can be referenced using `{{ variable_name }}` syntax:

```yaml
# Reference parameters
"{{ parameter_name }}"

# Reference previous step outputs
"{{ steps.step_id.outputs.output_name }}"

# Reference environment variables
"{{ env.ENV_VAR_NAME }}"

# Reference workflow variables
"{{ workflow.name }}"
```

#### Conditionals

Control step execution with conditions:

```yaml
conditions:
  # Always run
  - type: always

  # Run only if previous steps succeeded
  - type: on_success

  # Run only if previous step failed
  - type: on_failure

  # Run based on expression
  - type: conditional
    expression: "{{ create_tests }} == true"
```

---

## Workflow State Management

### State Tracking

The orchestrator maintains comprehensive state:

```python
@dataclass
class WorkflowState:
    workflow_id: str              # Workflow identifier
    current_step: str            # Currently executing step
    completed_steps: List[str]   # Successfully completed
    failed_steps: List[str]      # Failed steps
    step_results: Dict           # Detailed results
    variables: Dict              # Runtime variables
    status: str                  # Overall status
    started_at: datetime         # Start time
    completed_at: datetime       # End time
```

### Resume Capability

Workflows can be paused and resumed:

```python
# Save state
orchestrator.save_state('workflow_state.json')

# Later, resume
orchestrator.load_state('workflow_state.json')
orchestrator.resume(workflow)
```

### Rollback Mechanism

Define rollback procedures in workflow:

```yaml
rollback:
  - step_id: create_branch
    action: delete_branch

  - step_id: implement_feature
    action: revert_changes

  - step_id: deploy
    action: deploy_previous_version
```

Rollback is triggered when:
- Step fails with `on_error: rollback`
- Validation fails
- User manually triggers rollback

---

## Workflow Composition

### Concatenating Workflows

Workflows can be composed by referencing other workflows:

```yaml
workflow:
  name: full_feature_lifecycle

  steps:
    - id: develop
      name: Develop Feature
      workflow: feature_development  # Reference another workflow
      inputs:
        feature_name: "{{ feature_name }}"

    - id: review
      name: Code Review
      workflow: code_review
      inputs:
        pr_number: "{{ steps.develop.outputs.pr_number }}"

    - id: deploy
      name: Deploy
      workflow: deployment
      conditions:
        - type: on_success
```

### Dependency Management

Dependencies are automatically managed based on variable references. The orchestrator builds a dependency graph and executes steps in the correct order.

### Parallel Execution

Steps without dependencies can run in parallel:

```yaml
steps:
  - id: unit_tests
    name: Run Unit Tests
    skill: testing
    parallel_group: testing  # Group identifier

  - id: integration_tests
    name: Run Integration Tests
    skill: testing
    parallel_group: testing  # Same group = parallel

  - id: lint
    name: Run Linter
    skill: linting
    parallel_group: testing  # Runs in parallel

  - id: deploy
    name: Deploy
    skill: deployment
    # Waits for all steps in 'testing' group
```

### Error Recovery

Multiple error recovery strategies:

```yaml
on_error:
  # Continue to next step
  action: continue

  # Stop workflow
  action: stop

  # Retry with backoff
  action: retry

  # Execute rollback
  action: rollback

  # Execute fallback step
  action: fallback
  fallback_step: alternative_step_id
```

---

## Best Practices

1. **Keep workflows focused**: Each workflow should have a single, clear purpose
2. **Make workflows idempotent**: Re-running should be safe
3. **Include validation**: Always validate results
4. **Handle errors gracefully**: Define error handling for each step
5. **Document thoroughly**: Explain what each step does and why
6. **Use meaningful names**: Step IDs and names should be descriptive
7. **Version workflows**: Use semantic versioning
8. **Test workflows**: Create test cases for workflows
9. **Monitor execution**: Log progress and metrics
10. **Provide rollback**: Always define rollback procedures

---

## Conclusion

SkillForge workflows provide powerful orchestration capabilities for complex development tasks. By combining skills into workflows, you can automate entire development processes while maintaining flexibility, reliability, and observability.

For more information:
- See SKILLS.md for available skills
- See CONTEXTS.md for context management
- See MEMORY.md for memory and learning
