import httpx
import json

from main import WOLFRAM_ID

async def query_wolfram_alpha(query):
    base_url = "https://www.wolframalpha.com/api/v1/llm-api"
    params = {
        "input": query,
        "appid": WOLFRAM_ID
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(base_url, params=params)

    if response.status_code == 200:
        if response.text:
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                return {"error": "Failed to decode JSON", "response_text": response.text}
        else:
            return {"error": "Empty response from Wolfram Alpha"}
    elif response.status_code == 502:
        return {"error": "502 Bad Gateway from Wolfram Alpha"}
    else:
        return {"error": f"Failed to query Wolfram Alpha, received HTTP {response.status_code}"}