import json
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from cs_agent.a2a.types import (
    AgentCard,
    SendTaskRequest,
    GetTaskRequest,
    SendTaskStreamingRequest,
    SendTaskResponse,
    GetTaskResponse,
    SendTaskStreamingResponse,
    JSONRPCResponse,
)

logger = logging.getLogger(__name__)


class A2AServer:
    """FastAPI-based server implementing the A2A (Agent-to-Agent) JSON-RPC 2.0 protocol."""

    def __init__(self, agent_card: AgentCard, task_manager, host="localhost", port=8000):
        self.agent_card = agent_card
        self.task_manager = task_manager
        self.host = host
        self.port = port
        self.app = FastAPI()

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/.well-known/agent.json")
        async def get_agent_card():
            return self.agent_card.dict(exclude_none=True)

        @self.app.post("/rpc")
        async def handle_rpc(request: Request):
            body = {}
            try:
                body = await request.json()
                method = body.get("method")

                if not method:
                    return JSONResponse(
                        {
                            "jsonrpc": "2.0",
                            "id": body.get("id", 0),
                            "error": {"code": -32600, "message": "Invalid request: no method"},
                        }
                    )

                if method == "tasks/send":
                    request_obj = SendTaskRequest(**body)
                    response = await self.task_manager.on_send_task(request_obj)
                    return JSONResponse(response.dict(exclude_none=True))

                elif method == "tasks/sendSubscribe":
                    request_obj = SendTaskStreamingRequest(**body)
                    result = await self.task_manager.on_send_task_subscribe(request_obj)

                    if isinstance(result, JSONRPCResponse):
                        return JSONResponse(result.dict(exclude_none=True))

                    async def stream_generator():
                        async for resp in result:
                            yield f"data: {json.dumps(resp.dict(exclude_none=True))}\n\n"

                    return StreamingResponse(stream_generator(), media_type="text/event-stream")

                elif method == "tasks/get":
                    request_obj = GetTaskRequest(**body)
                    task_id = request_obj.params.get("id")
                    history_length = request_obj.params.get("historyLength", 0)

                    task = await self.task_manager.get_task(task_id, history_length)
                    if not task:
                        return JSONResponse(
                            {
                                "jsonrpc": "2.0",
                                "id": request_obj.id,
                                "error": {"code": -32000, "message": f"Task {task_id} not found"},
                            }
                        )

                    response = GetTaskResponse(id=request_obj.id, result=task)
                    return JSONResponse(response.dict(exclude_none=True))

                elif method == "tasks/cancel":
                    task_id = body.get("params", {}).get("id")
                    if not task_id:
                        return JSONResponse(
                            {
                                "jsonrpc": "2.0",
                                "id": body.get("id", 0),
                                "error": {"code": -32602, "message": "Invalid params: missing id"},
                            }
                        )

                    task = await self.task_manager.cancel_task(task_id)
                    if not task:
                        return JSONResponse(
                            {
                                "jsonrpc": "2.0",
                                "id": body.get("id", 0),
                                "error": {"code": -32000, "message": f"Task {task_id} not found"},
                            }
                        )

                    return JSONResponse(
                        {"jsonrpc": "2.0", "id": body.get("id", 0), "result": task.dict(exclude_none=True)}
                    )

                elif method == "tasks/pushNotification/set":
                    task_id = body.get("params", {}).get("id")
                    config = body.get("params", {}).get("pushNotificationConfig")

                    if not task_id or not config:
                        return JSONResponse(
                            {
                                "jsonrpc": "2.0",
                                "id": body.get("id", 0),
                                "error": {
                                    "code": -32602,
                                    "message": "Invalid params: missing id or pushNotificationConfig",
                                },
                            }
                        )

                    result = await self.task_manager.set_push_notification(task_id, config)
                    return JSONResponse({"jsonrpc": "2.0", "id": body.get("id", 0), "result": result})

                elif method == "tasks/pushNotification/get":
                    task_id = body.get("params", {}).get("id")

                    if not task_id:
                        return JSONResponse(
                            {
                                "jsonrpc": "2.0",
                                "id": body.get("id", 0),
                                "error": {"code": -32602, "message": "Invalid params: missing id"},
                            }
                        )

                    result = await self.task_manager.get_push_notification(task_id)
                    return JSONResponse({"jsonrpc": "2.0", "id": body.get("id", 0), "result": result})

                else:
                    return JSONResponse(
                        {
                            "jsonrpc": "2.0",
                            "id": body.get("id", 0),
                            "error": {"code": -32601, "message": f"Method not found: {method}"},
                        }
                    )

            except Exception as e:
                logger.error("Error handling request: %s", e)
                return JSONResponse(
                    {
                        "jsonrpc": "2.0",
                        "id": body.get("id", 0) if body else 0,
                        "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                    }
                )

    def start(self):
        import uvicorn

        logger.info("Starting A2A Server on %s:%s", self.host, self.port)
        uvicorn.run(self.app, host=self.host, port=self.port)
