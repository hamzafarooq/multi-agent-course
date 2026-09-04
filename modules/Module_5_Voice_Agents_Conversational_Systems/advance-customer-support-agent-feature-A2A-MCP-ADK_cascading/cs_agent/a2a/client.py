import uuid
import json
import logging

import aiohttp

logger = logging.getLogger(__name__)


async def call_a2a_agent(query: str, host: str, port: int, stream: bool = False) -> str:
    """Call an agent via the A2A JSON-RPC protocol.

    Args:
        query: The text query to send.
        host: Target hostname.
        port: Target port.
        stream: If True, use SSE streaming (tasks/sendSubscribe).

    Returns:
        The text response from the agent.
    """
    url = f"http://{host}:{port}/rpc"
    task_id = f"task-{uuid.uuid4()}"
    session_id = f"session-{uuid.uuid4()}"

    if stream:
        return await _call_stream(query, url, task_id, session_id)
    return await _call_sync(query, url, task_id, session_id)


async def _call_sync(query: str, url: str, task_id: str, session_id: str) -> str:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tasks/send",
        "params": {
            "id": task_id,
            "sessionId": session_id,
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": query}],
            },
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error("Error calling agent: %s", error_text)
                raise Exception(f"Error calling agent: {error_text}")

            result = await response.json()

            if "error" in result:
                logger.error("Agent returned error: %s", result["error"])
                raise Exception(f"Agent error: {result['error']['message']}")

            task_result = result.get("result", {})
            artifacts = task_result.get("artifacts", [])

            if artifacts:
                for part in artifacts[0].get("parts", []):
                    if part.get("type") == "text":
                        return part.get("text", "")

            status = task_result.get("status", {})
            message = status.get("message", {})
            for part in message.get("parts", []):
                if part.get("type") == "text":
                    return part.get("text", "")

            return ""


async def _call_stream(query: str, url: str, task_id: str, session_id: str) -> str:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tasks/sendSubscribe",
        "params": {
            "id": task_id,
            "sessionId": session_id,
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": query}],
            },
        },
    }

    result_text = ""

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error("Error calling agent: %s", error_text)
                raise Exception(f"Error calling agent: {error_text}")

            async for line in response.content:
                line = line.decode("utf-8").strip()

                if line.startswith("data: "):
                    data = json.loads(line[6:])

                    if "result" in data and "artifact" in data["result"]:
                        artifact = data["result"]["artifact"]
                        for part in artifact.get("parts", []):
                            if part.get("type") == "text":
                                result_text = part.get("text", "")

    return result_text
