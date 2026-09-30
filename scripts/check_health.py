"""Quick CLI health check utility for Global News Intelligence."""
import sys
import json
import httpx


def main():
    url = "http://localhost:8000/health"
    print(f"Checking Global News Intelligence health at {url}...")
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url)
            print(f"Status Code: {resp.status_code}")
            data = resp.json()
            print(json.dumps(data, indent=2))
            if data.get("status") in ["healthy", "degraded"]:
                print("\n[SUCCESS] Health check passed!")
                return 0
            else:
                print("\n[WARNING] System reported unhealthy status.")
                return 1
    except Exception as e:
        print(f"\n[ERROR] Could not connect to API: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
