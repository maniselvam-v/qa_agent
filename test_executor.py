import httpx
import json
import asyncio

async def test_stream():
    url = "http://127.0.0.1:8000/runs/execute"
    payload = {
        "test_files": None,
        "markers": None,
        "target_base_url": "http://127.0.0.1:8000"
    }

    print(f"📡 Sending POST request to {url}...")
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload, timeout=60.0) as response:
                response.raise_for_status()
                print("✅ Connection established! Streaming logs:\n" + "-"*50)
                
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        try:
                            # Drop the "data: " prefix and parse
                            data = json.loads(line[5:].strip())
                            
                            # Pretty print based on event type
                            if data["type"] == "log":
                                print(f"[{data['level']}] {data.get('message', '')}")
                            elif data["type"] == "result":
                                print("\n" + "="*50)
                                print("📊 FINAL RESULTS PAYLOAD:")
                                print(json.dumps(data, indent=2))
                            elif data["type"] == "done":
                                print("\n🏁 " + data.get("message", ""))
                            else:
                                print(f"RAW: {data}")
                        except json.JSONDecodeError:
                            print(f"[RAW STREAM CONTENT]: {line}")
    except httpx.ConnectError:
        print("❌ Cannot connect to server. Is Uvicorn running on port 8000?")
        print("Run: uvicorn src.qa_agent.main:app --reload")

if __name__ == "__main__":
    asyncio.run(test_stream())
