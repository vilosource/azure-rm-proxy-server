# GitFlow Workflow for Azure RM Proxy Server

This document outlines the GitFlow workflow used in the Azure RM Proxy Server project to help new developers understand our branching strategy, testing approach, and release process.

## Branching Strategy

We follow a modified GitFlow branching model with automated CI/CD integration. Here's how our branch structure works:

### Main Branches

- **`main`**: Represents production-ready code
  - Always stable and deployable
  - Tagged with version numbers for releases
  - Protected from direct commits
  
- **`develop`**: Integration branch for ongoing development
  - Contains the latest delivered development changes
  - Source for feature branches
  - May be unstable at times but should generally be working

### Supporting Branches

- **`feature/*`**: Used for developing new features
  - Always branched from: `develop`
  - Always merged back into: `develop` (automatically when tests pass)
  - Naming convention: `feature/descriptive-feature-name`

- **`release/*`**: Preparation for a new production release
  - Branched from: `develop`
  - Merged to: `main` (manually after approval)
  - Naming convention: `release/vX.Y.Z`
  - Only bug fixes and release preparations (version bumps, docs)

- **`hotfix/*`**: Emergency fixes for production issues
  - Branched from: `main`
  - Merged to: `main` AND `develop` (automatically when tests pass)
  - Naming convention: `hotfix/brief-description`

## Workflow for Different Tasks

### Starting a New Feature

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-new-feature
# Work on your feature...
git commit -m "feat: add new capability"
git push origin feature/my-new-feature
```

Once the feature branch is pushed and tests pass in CI, it will automatically be merged to `develop`.

### Creating a Release

```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0
# Make final adjustments, version bumps, documentation updates
git commit -m "chore: prepare v1.2.0 release"
git push origin release/v1.2.0
```

After thorough testing, the release branch is manually merged to `main` through a pull request.

### Fixing a Production Bug (Hotfix)

```bash
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-fix
# Fix the issue
git commit -m "fix: resolve critical issue"
git push origin hotfix/critical-bug-fix
```

Once the hotfix passes tests in CI, it will automatically be merged to both `main` and `develop`.

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) format which works with our semantic versioning process:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Common types include:
- `feat`: A new feature (minor version)
- `fix`: A bug fix (patch version)
- `docs`: Documentation only changes
- `style`: Changes that don't affect code meaning
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting tests
- `chore`: Changes to build process or auxiliary tools
- `feat!` or `fix!`: Breaking change (major version)

Example:
```
feat(vm): add ability to fetch VM power state

This adds a new API endpoint to retrieve the current power state of VMs.

BREAKING CHANGE: Changes response format of /api/vms endpoint
```

## Automated Testing & CI/CD

Our GitHub Actions workflow runs different tests based on branch type:

| Branch | Actions | Auto-merge |
|--------|---------|------------|
| `feature/*` | Unit tests, linting | ➡️ To `develop` |
| `develop` | Integration tests, code quality, linting, coverage | ❌ No |
| `release/*` | Integration tests, regression tests | ❌ No |
| `hotfix/*` | Critical tests, regression tests | ➡️ To `main` & `develop` |
| `main` | Final tests, security checks | ❌ No |

## Releases & Versioning

We use semantic versioning via semantic-release to automate version number determination:
- Patch releases (`x.y.Z`): Bug fixes
- Minor releases (`x.Y.z`): New features (backward compatible)
- Major releases (`X.y.z`): Breaking changes

When code is merged into `main`, our semantic-release process:
1. Analyzes commit messages
2. Determines the appropriate version increment
3. Updates the version number
4. Generates release notes in the CHANGELOG
5. Creates a git tag
6. Publishes to PyPI

## Getting Started for New Developers

1. Clone the repository
2. Create a feature branch from `develop`
3. Make your changes following our code style and commit conventions
4. Push your branch and create a PR against `develop` if needed
5. Once your tests pass, automated merging will take care of the rest

## Best Practices

- Keep feature branches short-lived (days, not weeks)
- Write meaningful commit messages that clearly explain changes
- Always pull the latest `develop` before creating a new branch
- Add tests for new features and bug fixes
- Update documentation when changing functionality

For questions about our workflow, please reach out to the project maintainers.