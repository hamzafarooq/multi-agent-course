from typing import List, Optional

from cs_agent.a2a.types import JSONRPCResponse, InvalidRequestError


def are_modalities_compatible(
    client_modalities: Optional[List[str]], agent_modalities: List[str]
) -> bool:
    """Check if the client's accepted modalities are compatible with the agent's supported modalities."""
    if not client_modalities:
        return True

    for modality in client_modalities:
        if modality in agent_modalities:
            return True

    return False


def new_incompatible_types_error(request_id: int) -> JSONRPCResponse:
    """Create a JSON-RPC error response for incompatible modality requests."""
    return JSONRPCResponse(
        id=request_id,
        error=InvalidRequestError(
            message="Incompatible modalities. The agent does not support any of the requested output modalities."
        ),
    )
