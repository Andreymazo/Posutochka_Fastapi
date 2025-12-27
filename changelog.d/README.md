# Changelog Fragments

This directory contains changelog fragments for upcoming releases.

## How to Use

When making changes that should be documented in the changelog:

1. Create a new `.md` file in this directory
2. Name it descriptively (e.g., `add-user-authentication.md` or `fix-enum-migration.md`)
3. Write a brief description of your changes

### Example Fragment

```markdown
### Added
- New user authentication system with JWT tokens

### Fixed
- Resolved PostgreSQL ENUM duplicate error in migrations
```

## Categories

Use these categories in your fragments:

- **Added** - New features
- **Changed** - Changes in existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security improvements

## Release Process

When a release is made, fragments are collected into CHANGELOG.md and removed from this directory.
