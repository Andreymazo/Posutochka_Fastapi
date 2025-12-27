# Contributing to Posutochka API

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/Andreymazo/Posutochka_Fastapi.git
   cd Posutochka_Fastapi
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**

   ```bash
   pip install pre-commit
   pre-commit install
   ```

5. **Set up the database**

   Copy `.env.example` to `.env` and configure your database URL:

   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

   Or use Docker Compose:

   ```bash
   docker-compose up -d
   ```

## Development Workflow

1. **Create a feature branch**

   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes**

   - Write code following the project's style guidelines
   - Add tests for any new functionality
   - Update documentation as needed

3. **Run quality checks**

   ```bash
   # Lint code
   ruff check .

   # Format code
   ruff format .

   # Type check
   mypy app --ignore-missing-imports

   # Run all checks together
   ruff check . && ruff format --check . && mypy app --ignore-missing-imports
   ```

4. **Run tests**

   ```bash
   # Run tests
   pytest

   # Run tests with coverage
   pytest --cov=app --cov-report=term --cov-report=html

   # Run tests with verbose output
   pytest -v --tb=short
   ```

5. **Commit your changes**

   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Pre-commit hooks will automatically run and check your code.

6. **Push and create a Pull Request**

   ```bash
   git push origin feature/my-feature
   ```

   Then create a Pull Request on GitHub.

## Code Style Guidelines

This project uses:

- **Ruff** for linting and formatting
- **mypy** for static type checking
- **pytest** for testing

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions and methods
- Write docstrings for all public APIs
- Keep functions focused and single-purpose
- Maintain test coverage for new code

### Commit Message Format

Use conventional commits format:

```
<type>: <description>

[optional body]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Testing Guidelines

- Write tests for all new features and bug fixes
- Use pytest fixtures for common setup
- Organize tests using classes when appropriate
- Use descriptive test names that explain what is being tested

Example test structure:

```python
class TestMyFeature:
    """Tests for my feature."""

    def test_basic_functionality(self, client: TestClient) -> None:
        """Test basic functionality."""
        response = client.get("/endpoint")
        assert response.status_code == 200

    def test_edge_case(self, client: TestClient) -> None:
        """Test edge case handling."""
        response = client.get("/endpoint?param=edge_value")
        assert response.status_code == 200
```

## Project Structure

```
.
├── .github/workflows/    # GitHub Actions CI/CD
├── alembic/              # Database migrations
├── app/
│   ├── main.py           # FastAPI application entry point
│   ├── database.py       # Database configuration
│   ├── models/           # SQLAlchemy ORM models
│   ├── routers/          # API endpoint routers
│   └── schemas/          # Pydantic validation schemas
├── tests/                # Test files
├── .pre-commit-config.yaml  # Pre-commit hooks
├── pyproject.toml        # Project configuration
├── requirements.txt      # Production dependencies
├── docker-compose.yml    # Docker setup
├── Dockerfile            # Docker image definition
└── README.md             # Project README
```

## Pull Request Process

1. Ensure all tests pass locally
2. Update documentation if needed
3. Ensure the PR description clearly describes the changes
4. Link any related issues in the PR description
5. Wait for CI checks to pass
6. Address any review feedback

## Running the Application

### Local Development

```bash
# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m app.main
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run only the database
docker-compose up postgres -d
```

### API Documentation

Once running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database Migrations

Use Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues and PRs before creating new ones

Thank you for contributing!
