from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel


class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    UNKNOWN = "unknown"


class TextPart(BaseModel):
    type: str = "text"
    text: str


class FilePart(BaseModel):
    type: str = "file"
    file: Dict[str, Any]


class DataPart(BaseModel):
    type: str = "data"
    data: Dict[str, Any]


Part = Union[TextPart, FilePart, DataPart]


class Message(BaseModel):
    role: str
    parts: List[Part]
    metadata: Dict[str, Any] = {}


class Artifact(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parts: List[Part]
    metadata: Dict[str, Any] = {}
    index: int
    append: Optional[bool] = False
    lastChunk: Optional[bool] = False


class TaskStatus(BaseModel):
    state: TaskState
    message: Optional[Message] = None
    timestamp: Optional[str] = None


class Task(BaseModel):
    id: str
    sessionId: str
    status: TaskStatus
    history: Optional[List[Message]] = None
    artifacts: Optional[List[Artifact]] = None
    metadata: Dict[str, Any] = {}


class TaskStatusUpdateEvent(BaseModel):
    id: str
    status: TaskStatus
    final: bool
    metadata: Optional[Dict[str, Any]] = None


class TaskArtifactUpdateEvent(BaseModel):
    id: str
    artifact: Artifact
    metadata: Optional[Dict[str, Any]] = None


class PushNotificationConfig(BaseModel):
    url: str
    token: Optional[str] = None
    authentication: Optional[Dict[str, Any]] = None


class TaskSendParams(BaseModel):
    id: str
    sessionId: Optional[str] = None
    message: Message
    historyLength: Optional[int] = None
    pushNotification: Optional[PushNotificationConfig] = None
    metadata: Dict[str, Any] = {}
    acceptedOutputModes: Optional[List[str]] = None


class AgentCapabilities(BaseModel):
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


class AgentProvider(BaseModel):
    organization: str
    url: str


class AgentAuthentication(BaseModel):
    schemes: List[str]
    credentials: Optional[str] = None


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    tags: List[str]
    examples: Optional[List[str]] = None
    inputModes: Optional[List[str]] = None
    outputModes: Optional[List[str]] = None


class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    provider: Optional[AgentProvider] = None
    version: str
    documentationUrl: Optional[str] = None
    capabilities: AgentCapabilities
    authentication: Optional[AgentAuthentication] = None
    defaultInputModes: List[str]
    defaultOutputModes: List[str]
    skills: List[AgentSkill]


# JSON-RPC related types

class InternalError(BaseModel):
    code: int = -32603
    message: str


class MethodNotFoundError(BaseModel):
    code: int = -32601
    message: str = "Method not found"


class InvalidRequestError(BaseModel):
    code: int = -32600
    message: str


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: int
    result: Optional[Any] = None
    error: Optional[Union[InternalError, MethodNotFoundError, InvalidRequestError]] = None


class SendTaskRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int
    method: str = "tasks/send"
    params: TaskSendParams


class SendTaskResponse(JSONRPCResponse):
    result: Task


class SendTaskStreamingRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int
    method: str = "tasks/sendSubscribe"
    params: TaskSendParams


class SendTaskStreamingResponse(JSONRPCResponse):
    result: Union[TaskStatusUpdateEvent, TaskArtifactUpdateEvent]


class GetTaskRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int
    method: str = "tasks/get"
    params: Dict[str, Any]


class GetTaskResponse(JSONRPCResponse):
    result: Task


class MissingAPIKeyError(Exception):
    pass
