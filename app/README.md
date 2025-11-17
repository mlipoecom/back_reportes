# Reports API

Backend API for an upload and download reports system web application.

## Description

FastAPI-based backend for managing files, companies, suppliers, and users with authentication and authorization.

## Prerequisites

- Python 3.13
- PostgreSQL database
- UV (for modern installation method) or pip (for traditional method)

## Installation

You can install and run this project using either **UV** (modern, recommended) or the **traditional approach** (venv + pip).

### Method 1: Using UV (Recommended)

UV is a fast Python package installer and resolver written in Rust.

#### Install UV

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Setup Project with UV

```bash
# Clone the repository (if not already cloned)
cd app

# Create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Activate virtual environment
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

### Method 2: Traditional Approach (venv + pip)

#### Setup Project Traditionally

```bash
# Clone the repository (if not already cloned)
cd app

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file or set environment variables with your database configuration and other settings. The application expects the following:

- Database connection details (see `config.py` and `database.py`)
- JWT secret keys for authentication
- SMTP settings for email functionality (if used)

## Running the Application

Once installed and configured, run the application with:

```bash
# Make sure your virtual environment is activated first

# Run with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or run with custom settings
uvicorn main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive API docs (Swagger)**: http://localhost:8000/docs
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc

## Project Structure

```
app/
├── routes/           # API route handlers
│   ├── auth.py      # Authentication endpoints
│   ├── companies.py # Company management
│   ├── files.py     # File upload/download
│   ├── suppliers.py # Supplier management
│   ├── users.py     # User management
│   └── ...
├── main.py          # FastAPI application entry point
├── database.py      # Database connection pool
├── models.py        # Data models
├── security.py      # Authentication & authorization
├── config.py        # Configuration settings
└── requirements.txt # Python dependencies
```

## Development

### Run in Development Mode

```bash
uvicorn main:app --reload
```

The `--reload` flag enables auto-reload on code changes.

### Update Dependencies

**With UV:**
```bash
uv pip compile requirements.txt
uv pip install -r requirements.txt
```

**Traditional:**
```bash
pip install -r requirements.txt --upgrade
```

## Technologies Used

- **FastAPI** - Modern web framework for building APIs
- **Uvicorn** - ASGI server
- **AsyncPG** - Async PostgreSQL driver
- **Python-JOSE** - JWT token handling
- **Bcrypt** - Password hashing
- **Pydantic** - Data validation

