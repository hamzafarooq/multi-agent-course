import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, AsyncIterable, Any, Union

from cs_agent.a2a.types import (
    SendTaskRequest,
    TaskSendParams,
    Message,
    TaskStatus,
    Artifact,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TextPart,
    TaskState,
    Task,
    SendTaskResponse,
    InternalError,
    JSONRPCResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
)
from cs_agent.a2a.utils import are_modalities_compatible, new_incompatible_types_error

logger = logging.getLogger(__name__)

SUPPORTED_MODES = ["text", "text/plain"]


class InMemoryTaskManager:
    """Base task manager with in-memory storage for A2A tasks."""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_messages: Dict[str, List[Message]] = {}
        self.push_notifications: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()

    async def upsert_task(self, params: TaskSendParams) -> Task:
        async with self.lock:
            task_id = params.id
            session_id = params.sessionId or str(uuid.uuid4())

            if task_id not in self.tasks:
                task = Task(
                    id=task_id,
                    sessionId=session_id,
                    status=TaskStatus(
                        state=TaskState.SUBMITTED,
                        timestamp=datetime.utcnow().isoformat(),
                    ),
                    history=[],
                    artifacts=[],
                )
                self.tasks[task_id] = task
                self.task_messages[task_id] = []
            else:
                task = self.tasks[task_id]

            message = params.message
            self.task_messages[task_id].append(message)
            task.history = (
                self.task_messages[task_id][-params.historyLength:]
                if params.historyLength
                else self.task_messages[task_id]
            )

            task.status = TaskStatus(
                state=TaskState.WORKING,
                timestamp=datetime.utcnow().isoformat(),
            )

            return task

    async def get_task(self, task_id: str, history_length: int = 0) -> Optional[Task]:
        async with self.lock:
            if task_id not in self.tasks:
                return None

            task = self.tasks[task_id]
            if history_length > 0 and task_id in self.task_messages:
                task.history = self.task_messages[task_id][-history_length:]
            else:
                task.history = self.task_messages.get(task_id, [])

            return task

    async def cancel_task(self, task_id: str) -> Optional[Task]:
        async with self.lock:
            if task_id not in self.tasks:
                return None

            task = self.tasks[task_id]
            task.status = TaskStatus(
                state=TaskState.CANCELED,
                timestamp=datetime.utcnow().isoformat(),
            )
            return task

    async def set_push_notification(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        self.push_notifications[task_id] = config
        return {"id": task_id, "pushNotificationConfig": config}

    async def get_push_notification(self, task_id: str) -> Dict[str, Any]:
        config = self.push_notifications.get(task_id)
        return {"id": task_id, "pushNotificationConfig": config}

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        raise NotImplementedError

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> Union[AsyncIterable[SendTaskStreamingResponse], JSONRPCResponse]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Concrete task managers
# ---------------------------------------------------------------------------

def _validate_request(request: Union[SendTaskRequest, SendTaskStreamingRequest]):
    task_send_params: TaskSendParams = request.params
    if not are_modalities_compatible(task_send_params.acceptedOutputModes, SUPPORTED_MODES):
        logger.warning(
            "Unsupported output mode. Received %s, Support %s",
            task_send_params.acceptedOutputModes,
            SUPPORTED_MODES,
        )
        return new_incompatible_types_error(request.id)
    return None


def _get_user_query(task_send_params: TaskSendParams) -> str:
    for part in task_send_params.message.parts:
        if isinstance(part, TextPart) or (isinstance(part, dict) and part.get("type") == "text"):
            return part.text if hasattr(part, "text") else part.get("text", "")
    raise ValueError("Only text parts are supported")


class _AgentTaskManager(InMemoryTaskManager):
    """Shared implementation for agent-specific task managers."""

    def __init__(self, agent_call):
        super().__init__()
        self.call_agent = agent_call

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        error = _validate_request(request)
        if error:
            return error

        await self.upsert_task(request.params)
        return await self._invoke(request)

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> Union[AsyncIterable[SendTaskStreamingResponse], JSONRPCResponse]:
        error = _validate_request(request)
        if error:
            return error

        await self.upsert_task(request.params)
        return self._stream_generator(request)

    async def _stream_generator(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse]:
        task_send_params: TaskSendParams = request.params
        query = _get_user_query(task_send_params)

        try:
            task_status = TaskStatus(state=TaskState.WORKING)
            yield SendTaskStreamingResponse(
                id=request.id,
                result=TaskStatusUpdateEvent(id=task_send_params.id, status=task_status, final=False),
            )

            result = await self.call_agent(query)

            parts = [{"type": "text", "text": result}]
            message = Message(role="agent", parts=parts)
            task_status = TaskStatus(state=TaskState.COMPLETED, message=message)

            artifacts = [Artifact(parts=parts, index=0, lastChunk=True)]
            await self._update_store(task_send_params.id, task_status, artifacts)

            yield SendTaskStreamingResponse(
                id=request.id,
                result=TaskArtifactUpdateEvent(id=task_send_params.id, artifact=artifacts[0]),
            )

            yield SendTaskStreamingResponse(
                id=request.id,
                result=TaskStatusUpdateEvent(id=task_send_params.id, status=task_status, final=True),
            )
        except Exception as e:
            logger.error("Error streaming response: %s", e)
            yield JSONRPCResponse(
                id=request.id,
                error=InternalError(message=f"Error streaming response: {str(e)}"),
            )

    async def _update_store(
        self, task_id: str, status: TaskStatus, artifacts: list[Artifact]
    ) -> Task:
        async with self.lock:
            try:
                task = self.tasks[task_id]
            except KeyError:
                logger.error("Task %s not found for update", task_id)
                raise ValueError(f"Task {task_id} not found")

            task.status = status
            if artifacts is not None:
                if task.artifacts is None:
                    task.artifacts = []
                task.artifacts.extend(artifacts)

            return task

    async def _invoke(self, request: SendTaskRequest) -> SendTaskResponse:
        task_send_params: TaskSendParams = request.params
        query = _get_user_query(task_send_params)

        try:
            result = await self.call_agent(query)
        except Exception as e:
            logger.error("Error invoking agent: %s", e)
            raise ValueError(f"Error invoking agent: {e}")

        parts = [{"type": "text", "text": result}]

        task = await self._update_store(
            task_send_params.id,
            TaskStatus(state=TaskState.COMPLETED, message=Message(role="agent", parts=parts)),
            [Artifact(parts=parts, index=0)],
        )

        return SendTaskResponse(id=request.id, result=task)


class JudgeTaskManager(_AgentTaskManager):
    def __init__(self, judge_agent_call):
        super().__init__(agent_call=judge_agent_call)


class MaskTaskManager(_AgentTaskManager):
    def __init__(self, mask_agent_call):
        super().__init__(agent_call=mask_agent_call)
