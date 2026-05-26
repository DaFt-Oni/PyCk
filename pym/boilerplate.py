import os
from pathlib import Path
from pym.utils import log_success, log_info

# .gitignore boilerplate
GITIGNORE = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
bin/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environments
.venv/
venv/
ENV/
env/

# System files
.DS_Store
Thumbs.db

# Environments variables
.env
.env.local

# IDEs and editors
.idea/
.vscode/
*.suo
*.ntvs*
*.njsproj
*.sln
*.swp

# Testing / coverage
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
"""

# Premium Multi-Stage Dockerfile
DOCKERFILE = """# --- Build Stage ---
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system utilities needed for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install uv for rapid dependency resolution in build stage
RUN pip install --no-cache-dir uv

# Copy package config to leverage Docker caching layers
COPY pyckage.json ./

# Create virtualenv and install production dependencies using uv
RUN uv venv .venv
# Parse pyckage.json and run uv pip install (PyCk wrapper equivalent)
RUN python -c "import json; d=json.load(open('pyckage.json')); pkgs=[f'{k}{v}' if v and v!='*' else k for k,v in d.get('dependencies', {}).items()]; import subprocess; len(pkgs) > 0 and subprocess.run(['uv', 'pip', 'install', '--python', '.venv/bin/python'] + pkgs)"

# --- Final Runtime Stage ---
FROM python:3.13-slim AS runner

WORKDIR /app

# Create a non-root system user for security
RUN groupadd -g 999 appuser && \\
    useradd -r -u 999 -g appuser appuser

# Copy virtual environment and app code
COPY --from=builder /app/.venv /app/.venv
COPY . /app

# Configure path variables to use venv immediately
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Fix permissions
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Command to execute (change default depending on framework)
CMD ["python", "main.py"]
"""

# Stunning formatted README.md
README_TEMPLATE = """# {project_name}

{description}

<p align="center">
  <img src="https://img.shields.io/badge/Powered%20By-PyCk-96ff7f?style=for-the-badge&logo=python" alt="PyCk Powered">
  <img src="https://img.shields.io/badge/Environment-.venv-blue?style=for-the-badge" alt="Environment">
  <img src="https://img.shields.io/badge/Python-3.13%2B-cyan?style=for-the-badge&logo=python" alt="Python Version">
</p>

---

## ⚡ Quickstart

This project is managed with **PyCk**, a high-performance Python package manager.

### 1. Synchronize Dependencies
To configure your local virtual environment and download all dependencies, run:
```bash
pym install
```

### 2. Launch Development Server
```bash
pym run dev
```

### 3. Run Testing Suite
```bash
pym run test
```

---

## 📁 Directory Structure
```
├── .venv/               # Isolated virtual environment (ignored by Git)
├── .env                 # Local secrets and environment variables
├── pyckage.json         # NPM-style project descriptor
├── pyckage.lock         # Pinned versions lockfile
├── main.py              # Main execution entrypoint
└── README.md            # Beautiful documentation
```

*Created with passion using PyCk & `pym` CLI.*
"""

# FASTAPI Boilerplate
FASTAPI_MAIN = """import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Read settings from auto-injected .env variables
PORT = int(os.environ.get("PORT", 8000))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

app = FastAPI(
    title="PyCk API",
    description="High-performance REST API managed by PyCk",
    version="0.1.0"
)

# Enable CORS headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "framework": "FastAPI",
        "environment": ENVIRONMENT,
        "features": ["NPM DX", "Auto .env injection", "Rust Speed via UV"]
    }

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}

if __name__ == "__main__":
    print(f"🚀 Launching server in {ENVIRONMENT} environment...")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=(ENVIRONMENT == "development"))
"""

FASTAPI_TEST = """from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["framework"] == "FastAPI"
"""

# FLASK Boilerplate
FLASK_MAIN = """import os
from flask import Flask, jsonify

app = Flask(__name__)

# Read config from auto-loaded .env variables
PORT = int(os.environ.get("PORT", 8000))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

@app.route("/")
def index():
    return jsonify({
        "status": "healthy",
        "framework": "Flask",
        "environment": ENVIRONMENT,
        "details": "Managed cleanly using PyCk package manager"
    })

if __name__ == "__main__":
    print(f"🚀 Running Flask on http://localhost:{PORT} in {ENVIRONMENT} mode...")
    app.run(host="0.0.0.0", port=PORT, debug=(ENVIRONMENT == "development"))
"""

FLASK_TEST = """import pytest
from main import app as flask_app

@pytest.fixture
def client():
    with flask_app.test_client() as client:
        yield client

def test_index_route(client):
    res = client.get("/")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["status"] == "healthy"
    assert json_data["framework"] == "Flask"
"""

# Modern Minimal Single-File Django Boilerplate (great for rapid microservice prototyping!)
DJANGO_MAIN = """import os
import sys
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import JsonResponse
from django.urls import path

PORT = int(os.environ.get("PORT", 8000))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

# Django settings initialization
if not settings.configured:
    settings.configure(
        DEBUG=(ENVIRONMENT == "development"),
        SECRET_KEY=os.environ.get("SECRET_KEY", "pyck-django-secret-key-placeholder-3882717"),
        ROOT_URLCONF=__name__,
        MIDDLEWARE=[
            "django.middleware.common.CommonMiddleware",
        ],
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
        ],
    )

# Views
def api_root(request):
    return JsonResponse({
        "status": "healthy",
        "framework": "Django",
        "environment": ENVIRONMENT,
        "architecture": "Single-File Modern Blueprint"
    })

# Routing
urlpatterns = [
    path("", api_root),
]

app = get_wsgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    # Add port option automatically if running runserver
    args = sys.argv
    if len(args) > 1 and args[1] == "runserver" and len(args) == 2:
        args.append(f"0.0.0.0:{PORT}")
        
    execute_from_command_line(args)
"""

DJANGO_TEST = """from django.test import SimpleTestCase
from django.test import Client

class DjangoApiTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_root_view(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
"""

# Simple Main execution boilerplate
SIMPLE_MAIN = """import os
import sys

def main():
    # Environment variable automatic loading verification
    env_name = os.environ.get("ENVIRONMENT", "production")
    print(f"\\033[92m✔\\033[0m PyCk App successfully launched in \\033[1m{env_name}\\033[0m mode!")
    print(f"Python interpreter path: {sys.executable}")
    
if __name__ == "__main__":
    main()
"""

SIMPLE_TEST = """def test_simple_assertion():
    assert 1 + 1 == 2
"""

def scaffold_project(
    root_path: Path,
    name: str,
    description: str,
    framework: str,
    use_docker: bool,
    use_ruff: bool,
    use_pytest: bool,
    use_gitignore: bool = True
):
    """
    Creates premium file structure based on selected features.
    """
    # 1. Write README.md
    readme_path = root_path / "README.md"
    readme_content = README_TEMPLATE.format(project_name=name, description=description)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    # 2. Write .gitignore
    if use_gitignore:
        gitignore_path = root_path / ".gitignore"
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(GITIGNORE)
        
    # 3. Write .env file
    env_path = root_path / ".env"
    env_lines = [
        "# Configuration environment loaded automatically by PyCk",
        f"ENVIRONMENT=development",
        f"PORT=8000",
        f"SECRET_KEY=pyck_sec_{os.urandom(16).hex()}",
    ]
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(env_lines) + "\n")
        
    # 4. Generate Main file and test file
    main_path = root_path / "main.py"
    test_path = root_path / "test_main.py"
    
    if framework == "FastAPI":
        main_content = FASTAPI_MAIN
        test_content = FASTAPI_TEST
    elif framework == "Flask":
        main_content = FLASK_MAIN
        test_content = FLASK_TEST
    elif framework == "Django":
        main_content = DJANGO_MAIN
        test_content = DJANGO_TEST
    else:
        main_content = SIMPLE_MAIN
        test_content = SIMPLE_TEST
        
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(main_content)
        
    if use_pytest:
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_content)
            
    # 5. Write Dockerfile
    if use_docker:
        docker_path = root_path / "Dockerfile"
        # Adjust entrypoint if Django
        docker_content = DOCKERFILE
        if framework == "Django":
            docker_content = DOCKERFILE.replace(
                'CMD ["python", "main.py"]',
                'CMD ["python", "main.py", "runserver"]'
            )
        with open(docker_path, "w", encoding="utf-8") as f:
            f.write(docker_content)
            
    # 6. Append Ruff tool config to pyproject.toml if selected
    if use_ruff:
        # We will write/append ruff rules block to the PyCk target pyproject.toml
        # Note: the target project gets its own empty pyproject.toml OR we put it in pyckage.json under "tool" if desired.
        # Standard: put ruff config block in pyproject.toml in project root.
        target_pyproject = root_path / "pyproject.toml"
        ruff_block = """
[tool.ruff]
line-length = 88
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = []
"""
        with open(target_pyproject, "w", encoding="utf-8") as f:
            f.write(ruff_block)
            
    log_success(f"Project structure successfully scaffolded at {root_path}!")
