import urllib.request
import json


def verify_user(api_url: str):
    """Call API and return JSON response directly, with error handling."""
    try:
        with urllib.request.urlopen(api_url) as response:
            if response.status != 200:
                return {
                    "exists": False,
                    "message": f"Error: HTTP {response.status}",
                    "url": api_url,
                }

            data = response.read()
            return json.loads(data.decode("utf-8"))

    except Exception as e:
        return {"exists": False, "message": f"Unexpected error: {e}", "url": api_url}


def post_error(api_url: str, payload: dict):
    """Send POST request with JSON payload and return response, with error handling."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                return {
                    "success": False,
                    "message": f"Error: HTTP {response.status}",
                    "url": api_url,
                }

            response_data = response.read()
            return json.loads(response_data.decode("utf-8"))

    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}", "url": api_url}


# Example usage
if __name__ == "__main__":
    url = "http://127.0.0.1:9999/api/verify"
    result = verify_user(url)
    print(result)

