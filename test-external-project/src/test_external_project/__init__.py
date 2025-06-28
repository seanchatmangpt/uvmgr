"""Test external project for uvmgr validation."""

__version__ = "0.1.0"


def hello_world():
    """Simple function for testing."""
    return "Hello, World!"


def add_numbers(a, b):
    """Add two numbers."""
    return a + b


def fetch_data():
    """Simulate data fetching with requests."""
    import requests
    try:
        response = requests.get("https://httpbin.org/json", timeout=5)
        return response.json()
    except Exception as e:
        return {"error": str(e)}