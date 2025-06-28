
import requests


def get_python_org():
    """Simple function that makes HTTP request."""
    try:
        response = requests.get("https://httpbin.org/json")
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def calculate_sum(a, b):
    """Simple calculation function."""
    return a + b

if __name__ == "__main__":
    result = get_python_org()
    print(f"Result: {result}")
    print(f"Sum: {calculate_sum(5, 3)}")
