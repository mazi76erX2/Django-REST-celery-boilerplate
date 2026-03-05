# Django REST Boilerplate

An asynchronous API using Django REST Framework.

## Table of Contents

- [Django REST Boilerplate](#django-rest-boilerplate)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Installation](#installation)
    - [Local Setup with uv](#local-setup-with-uv)
      - [Running Celery Locally](#running-celery-locally)
    - [Docker Setup with Watch Mode](#docker-setup-with-watch-mode)
  - [Usage](#usage)
    - [Local Development](#local-development)
    - [Docker Development](#docker-development)
  - [Testing](#testing)
    - [Local Testing](#local-testing)
    - [Docker Testing](#docker-testing)
  - [Code Quality](#code-quality)
  - [Deployment](#deployment)
    - [Docker Production Deployment](#docker-production-deployment)
    - [SSL Certificates with Let's Encrypt](#ssl-certificates-with-lets-encrypt)
    - [AWS Deployment](#aws-deployment)
  - [Project Structure](#project-structure)
  - [Makefile Commands](#makefile-commands)
    - [Installation](#installation-1)
    - [Local Development](#local-development-1)
    - [Testing](#testing-1)
    - [Code Quality](#code-quality-1)
    - [Docker Development](#docker-development-1)
    - [Docker Production](#docker-production)
    - [Utilities](#utilities)
  - [Configuration](#configuration)
    - [Environment Variables](#environment-variables)
  - [Tech Stack](#tech-stack)
  - [Justifications](#justifications)
  - [Contributing](#contributing)
  - [License](#license)

## Features

- **Asynchronous Django** - Built with async views and ADRF for high performance
- **Django REST Framework** - Powerful and flexible API toolkit
- **OpenAPI/Swagger** - Auto-generated API documentation
- **Docker with Watch Mode** - Hot-reload during development without rebuilding containers
- **uv Package Manager** - Lightning-fast dependency management (10-100x faster than pip)
- **Valkey** - Redis-compatible in-memory data store for caching
- **PostgreSQL** - Robust relational database
- **Pre-commit Hooks** - Automated code quality checks
- **Type Hints** - Full type annotation support with mypy
- **Modern Tooling** - Black, isort, ruff, and pytest

## Requirements

- Python 3.13+
- Docker and Docker Compose
- uv (will be installed automatically)
- PostgreSQL (for local development without Docker)

## Installation

### Local Setup with uv

1. **Clone the repository:**
```bash
    git clone https://github.com/yourusername/django-rest-boilerplate.git
    cd django-rest-boilerplate
```

2. **Install uv (if not already installed):**
```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
```

    Or using the Makefile:
```bash
    make install
```

3. **Install dependencies:**
```bash
    uv sync --all-extras
```

    Or using the Makefile:
```bash
    make install-dev
```

4. **Copy environment file:**
```bash
    cp .env.example .env
```

    Or using the Makefile:
```bash
    make copy-env
```

5. **Create and configure the database:**

    - **For Linux:**
```bash
        make create-db-linux
```

    - **For Mac:**
```bash
        make create-db-mac
```

6. **Run migrations:**
```bash
    make migrate
```

7. **Start the development server:**
```bash
    make run
```

    The API will be available at `http://localhost:8000`

8. **Celery & Channels:**

#### Running Celery Locally

```bash
# Start Celery worker
make celery-worker

# Start Celery beat (scheduled tasks)
make celery-beat

# Start Flower (monitoring UI)
make celery-flower

### Docker Setup
```

1. **Copy environment file:**
```bash
    make copy-env
```

2. **Build and run the Docker containers:**
```bash
    make up
```

3. **View logs:**
```bash
    make logs
```

The API will be available at `http://localhost:8000`

### Docker Setup with Watch Mode

Watch mode automatically syncs your code changes to the container without rebuilding:
```bash
make watch
```

This enables:

- **Automatic code syncing** - Changes to Python files are instantly reflected
- **Automatic rebuilds** - Changes to pyproject.toml or uv.lock trigger a rebuild

## Usage

### Local Development
```bash
# Run migrations and start the server
make run-local

# Or run them separately
make migrate
make run

# Create a superuser
make superuser

# Open Django shell
make shell-django

# Create new migrations
make makemigrations
```

### Docker Development
```bash
# Start with watch mode (recommended)
make watch

# Or start in background
make up

# View logs
make logs
make logs-backend  # Backend only

# Open a shell in the container
make shell-docker

# Run migrations
make migrate-docker

# Restart containers
make restart

# Stop containers
make down

# Stop and remove volumes
make down-v
```

## Testing

### Local Testing
```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run tests in fast mode (stops on first failure)
make test-fast

# Run tests in watch mode
make test-watch
```

### Docker Testing
```bash
# Run tests inside Docker
make test-docker
```

## Code Quality
```bash
# Format code with black and isort
make format

# Check formatting without changes
make format-check

# Lint with ruff
make lint

# Lint and auto-fix issues
make lint-fix

# Run type checking with mypy
make typecheck

# Run all checks (format, lint, typecheck)
make check

# Format and fix all issues
make check-fix

# Run pre-commit hooks
make pre-commit

# Install pre-commit hooks
make pre-commit-install
```

## Deployment

### Docker Production Deployment

1. **Configure environment variables:**

    Update `.env` with production values:
```bash
    DEBUG=false
    SECRET_KEY=your-secure-secret-key
    ALLOWED_HOST_DNS=yourdomain.com www.yourdomain.com
```

2. **Build and start production containers:**
```bash
    make prod-up
```

3. **Run migrations:**
```bash
    make prod-migrate
```

4. **View logs:**
```bash
    make prod-logs
```

5. **Stop production containers:**
```bash
    make prod-down
```

### SSL Certificates with Let's Encrypt

1. **Update the domains in `scripts/init-letsencrypt.sh`:**
```bash
    domains=(yourdomain.com www.yourdomain.com)
    email="your-email@example.com"
    staging=0  # Set to 1 for testing
```

2. **Update `docker/nginx/nginx.conf` with your domain.**

3. **Initialize SSL certificates:**
```bash
    make ssl-init
```

    Certificates will auto-renew. To manually renew:
```bash
    make ssl-renew
```

### AWS Deployment

1. **Configure AWS credentials and update `.env`:**
```bash
    AWS_ACCOUNT_ID=your-account-id
    AWS_REGION=your-region
    AWS_ACCOUNT_URI=your-ecr-uri
```

2. **Build and push to AWS ECR:**
```bash
    make aws-push
```

## Project Structure
```text
├── backend/
│   ├── __init__.py
│   ├── manage.py
│   └── server/
│       ├── __init__.py
│       ├── asgi.py
│       ├── urls.py
│       ├── wsgi.py
│       └── settings/
│           ├── __init__.py
│           ├── base.py
│           ├── local.py
│           └── prod.py
├── docker/
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── Dockerfile.prod
│   │   ├── entrypoint.sh
│   │   └── entrypoint.prod.sh
│   └── nginx/
│       ├── Dockerfile
│       └── nginx.conf
├── example_app/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   ├── management/
│   ├── migrations/
│   └── tests/
├── scripts/
│   ├── format.sh
│   ├── init-letsencrypt.sh
│   ├── lint.sh
│   └── test.sh
├── .github/
│   └── workflows/
│       └── format-and-lint.yml
├── docker-compose.yml
├── docker-compose.prod.yml
├── docker-compose-debug.yml
├── pyproject.toml
├── uv.lock
├── Makefile
├── .env.example
├── .pre-commit-config.yaml
└── README.md
```

## Makefile Commands

### Installation

| Command | Description |
|---------|-------------|
| `make install` | Install uv and project dependencies |
| `make install-dev` | Install development dependencies |
| `make lock` | Lock dependencies |
| `make update` | Update all dependencies |
| `make copy-env` | Copy environment example file |

### Local Development

| Command | Description |
|---------|-------------|
| `make run` | Run the development server |
| `make run-local` | Run migrations and start the server |
| `make migrate` | Run database migrations |
| `make makemigrations` | Create new migrations |
| `make shell-django` | Open Django shell |
| `make superuser` | Create a superuser |
| `make collectstatic` | Collect static files |

### Testing

| Command | Description |
|---------|-------------|
| `make test` | Run tests |
| `make test-cov` | Run tests with coverage report |
| `make test-fast` | Run tests without coverage (faster) |
| `make test-watch` | Run tests in watch mode |

### Code Quality

| Command | Description |
|---------|-------------|
| `make format` | Format code with black and isort |
| `make format-check` | Check code formatting |
| `make lint` | Lint code with ruff |
| `make lint-fix` | Lint and fix code with ruff |
| `make typecheck` | Run mypy type checking |
| `make check` | Run all code quality checks |
| `make check-fix` | Format and fix all issues |
| `make pre-commit` | Run pre-commit hooks |
| `make pre-commit-install` | Install pre-commit hooks |

### Docker Development

| Command | Description |
|---------|-------------|
| `make up` | Build and start Docker containers |
| `make watch` | Start with watch mode (auto-reload) |
| `make down` | Stop Docker containers |
| `make down-v` | Stop containers and remove volumes |
| `make restart` | Restart Docker containers |
| `make logs` | View container logs |
| `make logs-backend` | View backend container logs |
| `make shell-docker` | Open shell in backend container |
| `make test-docker` | Run tests in Docker |
| `make migrate-docker` | Run migrations in Docker |
| `make debug-up` | Start debug containers |
| `make debug-down` | Stop debug containers |

### Docker Production

| Command | Description |
|---------|-------------|
| `make prod-up` | Start production containers |
| `make prod-down` | Stop production containers |
| `make prod-down-v` | Stop and remove volumes |
| `make prod-logs` | View production logs |
| `make prod-migrate` | Run production migrations |
| `make prod-shell` | Open shell in production container |
| `make prod-restart` | Restart production containers |
| `make ssl-init` | Initialize SSL certificates |
| `make ssl-renew` | Renew SSL certificates |

### Utilities

| Command | Description |
|---------|-------------|
| `make clean` | Clean cache and build files |
| `make clean-docker` | Remove all Docker resources |
| `make status` | Show Docker container status |
| `make health` | Check health of services |
| `make info` | Show project info |
| `make help` | Show all available commands |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `true` |
| `SECRET_KEY` | Django secret key | - |
| `ALLOWED_HOST_DNS` | Allowed hosts (space-separated) | `0.0.0.0 localhost 127.0.0.1` |
| `DATABASE_NAME` | Database name | `django-app` |
| `DATABASE_USERNAME` | Database username | `postgres` |
| `DATABASE_PASSWORD` | Database password | `postgres` |
| `DATABASE_HOST` | Database host | `db` |
| `DATABASE_PORT` | Database port | `5432` |
| `CACHE_HOST` | Valkey/Redis host | `valkey` |
| `CACHE_PORT` | Valkey/Redis port | `6379` |
| `PGADMIN_DEFAULT_EMAIL` | PgAdmin email | - |
| `PGADMIN_DEFAULT_PASSWORD` | PgAdmin password | - |

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Django 5.1 | Web framework |
| Django REST Framework | API toolkit |
| ADRF | Async DRF support |
| PostgreSQL 17 | Database |
| Valkey | Caching (Redis-compatible) |
| uv | Package manager |
| Docker | Containerization |
| Nginx | Reverse proxy |
| Gunicorn | WSGI server |
| Uvicorn | ASGI server |
| Black | Code formatter |
| Ruff | Linter |
| mypy | Type checker |
| pytest | Testing framework |
| drf-yasg | OpenAPI/Swagger docs |

## Justifications

**Django REST Framework**: A powerful and flexible toolkit for building Web APIs. It is well-documented with a large community, making it easy to find solutions to common problems.

**OpenAPI/Swagger**: Provides a standard way to describe APIs, making them easier to understand and work with. It also provides tools for generating client libraries and documentation.

**uv**: A blazingly fast Python package manager written in Rust. It's 10-100x faster than pip and provides better dependency resolution.

**Docker with Watch Mode**: Enables hot-reloading during development without rebuilding containers, significantly improving the development experience.

**Valkey**: A Redis-compatible in-memory data store. It's a community-driven fork of Redis with identical API compatibility, used for caching to speed up responses.

**Ruff**: An extremely fast Python linter written in Rust, replacing traditional tools like pylint and flake8 with better performance.

**Pre-commit Hooks**: Ensures code quality by running checks before each commit, catching issues early in the development process.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Install pre-commit hooks (`make pre-commit-install`)
4. Make your changes
5. Run checks (`make check`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
