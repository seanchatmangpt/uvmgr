#!/usr/bin/env python3
"""
Create a production-ready external project for uvmgr validation.
This creates a realistic FastAPI project to test external project support.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

def create_fastapi_project(base_dir: Path) -> Path:
    """Create a realistic FastAPI external project."""
    project_dir = base_dir / "fastapi-external-project"
    project_dir.mkdir()
    
    # Create pyproject.toml with realistic dependencies
    pyproject_content = """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "fastapi-external-project"
version = "0.1.0"
description = "Production FastAPI project for uvmgr external validation"
authors = [{name = "External Team", email = "team@external.com"}]
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "httpx>=0.25.0",
]
requires-python = ">=3.8"

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "mypy>=1.7.0",
    "ruff>=0.1.0",
]

[project.scripts]
fastapi-app = "fastapi_external_project.main:start_server"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
asyncio_mode = "auto"

[tool.black]
line-length = 88
target-version = ['py38']

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.ruff]
line-length = 88
target-version = "py38"
select = ["E", "W", "F", "I", "N", "UP"]
"""
    
    (project_dir / "pyproject.toml").write_text(pyproject_content)
    
    # Create main application
    src_dir = project_dir / "fastapi_external_project"
    src_dir.mkdir()
    
    (src_dir / "__init__.py").write_text("# FastAPI External Project")
    
    # Main FastAPI application
    main_content = '''#!/usr/bin/env python3
"""FastAPI external project main application."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(
    title="FastAPI External Project",
    description="Production FastAPI app for uvmgr external validation",
    version="0.1.0"
)

class Item(BaseModel):
    """Item model."""
    id: int
    name: str
    description: Optional[str] = None
    price: float

# In-memory storage for demo
items_db: List[Item] = []

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "FastAPI External Project running with uvmgr!"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "uvmgr_integrated": True}

@app.get("/items", response_model=List[Item])
async def get_items():
    """Get all items."""
    return items_db

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    """Create a new item."""
    items_db.append(item)
    return item

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """Get item by ID."""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

def start_server():
    """Start the FastAPI server."""
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_server()
'''
    (src_dir / "main.py").write_text(main_content)
    
    # Create comprehensive tests
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    
    test_content = '''#!/usr/bin/env python3
"""Comprehensive tests for FastAPI external project."""

import pytest
from fastapi.testclient import TestClient
from fastapi_external_project.main import app, items_db, Item

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    """Clear database before each test."""
    items_db.clear()

def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "uvmgr" in data["message"]

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["uvmgr_integrated"] is True

def test_create_and_get_item():
    """Test creating and retrieving items."""
    item_data = {
        "id": 1,
        "name": "Test Item",
        "description": "A test item",
        "price": 10.99
    }
    
    # Create item
    response = client.post("/items", json=item_data)
    assert response.status_code == 200
    created_item = response.json()
    assert created_item["name"] == "Test Item"
    
    # Get all items
    response = client.get("/items")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["name"] == "Test Item"
    
    # Get specific item
    response = client.get("/items/1")
    assert response.status_code == 200
    item = response.json()
    assert item["name"] == "Test Item"

def test_get_nonexistent_item():
    """Test getting non-existent item."""
    response = client.get("/items/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_multiple_items():
    """Test multiple items workflow."""
    items = [
        {"id": 1, "name": "Item 1", "price": 10.0},
        {"id": 2, "name": "Item 2", "price": 20.0},
        {"id": 3, "name": "Item 3", "price": 30.0},
    ]
    
    # Create multiple items
    for item in items:
        response = client.post("/items", json=item)
        assert response.status_code == 200
    
    # Verify all items exist
    response = client.get("/items")
    assert response.status_code == 200
    retrieved_items = response.json()
    assert len(retrieved_items) == 3
    
    # Verify individual items
    for i, item in enumerate(items, 1):
        response = client.get(f"/items/{i}")
        assert response.status_code == 200
        retrieved_item = response.json()
        assert retrieved_item["name"] == f"Item {i}"

@pytest.mark.asyncio
async def test_app_import():
    """Test that the app can be imported."""
    from fastapi_external_project.main import app
    assert app is not None
    assert app.title == "FastAPI External Project"
'''
    (tests_dir / "test_main.py").write_text(test_content)
    
    # Create API tests
    api_test_content = '''#!/usr/bin/env python3
"""API integration tests."""

import pytest
from fastapi.testclient import TestClient
from fastapi_external_project.main import app

client = TestClient(app)

def test_api_documentation():
    """Test that API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi_spec = response.json()
    assert openapi_spec["info"]["title"] == "FastAPI External Project"

def test_api_endpoints_exist():
    """Test that all expected endpoints exist."""
    response = client.get("/openapi.json")
    openapi_spec = response.json()
    paths = openapi_spec["paths"]
    
    expected_paths = ["/", "/health", "/items", "/items/{item_id}"]
    for path in expected_paths:
        assert path in paths or any(path.replace("{item_id}", "{item_id}") in p for p in paths)

def test_cors_and_headers():
    """Test CORS and headers."""
    response = client.get("/")
    assert response.status_code == 200
    # Basic header checks
    assert "content-type" in response.headers
'''
    (tests_dir / "test_api.py").write_text(api_test_content)
    
    # Create performance tests
    perf_test_content = '''#!/usr/bin/env python3
"""Performance tests for FastAPI external project."""

import pytest
import time
from fastapi.testclient import TestClient
from fastapi_external_project.main import app, items_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    """Clear database before each test."""
    items_db.clear()

def test_response_time():
    """Test that response times are reasonable."""
    start_time = time.time()
    response = client.get("/")
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # Should respond in under 1 second

def test_bulk_operations():
    """Test bulk operations performance."""
    # Create 100 items
    items = [{"id": i, "name": f"Item {i}", "price": float(i)} for i in range(1, 101)]
    
    start_time = time.time()
    for item in items:
        response = client.post("/items", json=item)
        assert response.status_code == 200
    end_time = time.time()
    
    # Should create 100 items in reasonable time
    assert (end_time - start_time) < 10.0
    
    # Verify all items were created
    response = client.get("/items")
    assert response.status_code == 200
    retrieved_items = response.json()
    assert len(retrieved_items) == 100

def test_concurrent_access():
    """Test handling of concurrent requests."""
    import concurrent.futures
    
    def make_request():
        return client.get("/health")
    
    # Make 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        responses = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # All requests should succeed
    for response in responses:
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
'''
    (tests_dir / "test_performance.py").write_text(perf_test_content)
    
    # Create README
    readme_content = '''# FastAPI External Project

Production-ready FastAPI application for testing uvmgr external project support.

## Features

- FastAPI web framework
- Pydantic data validation
- Comprehensive test suite
- Performance testing
- API documentation
- Health check endpoints

## Development with uvmgr

This project demonstrates uvmgr integration with external projects:

```bash
# Run tests
uvmgr tests run

# Run tests with coverage
uvmgr tests coverage

# Check OTEL integration
uvmgr otel test

# Validate Weaver semantic conventions
uvmgr weaver check

# Run linting
uvmgr lint check

# Build distribution
uvmgr build dist
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /items` - List all items
- `POST /items` - Create new item
- `GET /items/{item_id}` - Get item by ID
- `GET /docs` - API documentation

## Testing

Comprehensive test suite includes:
- Unit tests for all endpoints
- Integration tests
- Performance tests
- Concurrent access tests

## uvmgr Integration

This project validates that uvmgr works correctly with external FastAPI projects,
providing full OTEL instrumentation, semantic conventions, and development workflows.
'''
    (project_dir / "README.md").write_text(readme_content)
    
    return project_dir

def test_uvmgr_in_external_project(project_dir: Path) -> bool:
    """Test uvmgr functionality in the external FastAPI project."""
    os.chdir(project_dir)
    
    tests = [
        ("tests run", ["uvmgr", "tests", "run"]),
        ("otel test", ["uvmgr", "otel", "test"]),
        ("weaver check", ["uvmgr", "weaver", "check"]),
        ("tests coverage", ["uvmgr", "tests", "coverage"]),
    ]
    
    results = {}
    
    for test_name, cmd in tests:
        print(f"🧪 Testing: {test_name}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"✅ {test_name}: PASSED")
                results[test_name] = "PASSED"
            else:
                print(f"❌ {test_name}: FAILED")
                print(f"   Error: {result.stderr[:200]}...")
                results[test_name] = "FAILED"
        except subprocess.TimeoutExpired:
            print(f"⏱️ {test_name}: TIMEOUT")
            results[test_name] = "TIMEOUT"
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results[test_name] = "ERROR"
    
    # Summary
    passed = sum(1 for status in results.values() if status == "PASSED")
    total = len(results)
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    for test_name, status in results.items():
        status_emoji = "✅" if status == "PASSED" else "❌"
        print(f"   {status_emoji} {test_name}: {status}")
    
    return passed == total

def main():
    """Main function to create and test external project."""
    print("🎯 Creating production-ready external FastAPI project")
    print("=" * 60)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        try:
            # Create FastAPI project
            print("📁 Creating FastAPI external project...")
            project_dir = create_fastapi_project(temp_path)
            print(f"✅ Project created at: {project_dir}")
            print(f"📝 Project structure:")
            for item in sorted(project_dir.rglob("*")):
                if item.is_file():
                    rel_path = item.relative_to(project_dir)
                    print(f"   {rel_path}")
            
            # Test uvmgr functionality
            print(f"\n🧪 Testing uvmgr in external FastAPI project...")
            success = test_uvmgr_in_external_project(project_dir)
            
            if success:
                print("\n🎉 All external project tests PASSED!")
                print("✅ uvmgr works perfectly with external FastAPI projects")
                print("🚀 Production-ready external project support validated!")
                return 0
            else:
                print("\n❌ Some external project tests FAILED!")
                print("🔧 External project support needs refinement")
                return 1
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())