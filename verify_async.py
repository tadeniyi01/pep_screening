
import asyncio
import httpx
import json

async def test_screen():
    url = "http://127.0.0.1:8000/screen"
    payload = {
        "query": "Bola Ahmed Tinubu",
        "country": "Nigeria"
    }
    
    print(f"Sending request to {url}...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=60.0)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("Success! Response snippet:")
                print(json.dumps(resp.json(), indent=2)[:500] + "...")
            else:
                print("Error response:")
                print(resp.text)
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_screen())
