from cs_agent.a2a.server import A2AServer
from cs_agent.a2a.task_manager import JudgeTaskManager, MaskTaskManager
from cs_agent.a2a.types import AgentCard, AgentCapabilities, AgentSkill


def create_judge_server(host="localhost", port=10002, call_judge_agent=None) -> A2AServer:
    """Create and return an A2A server for the security judge agent."""
    if not call_judge_agent:
        raise ValueError("Judge agent callback function is required")

    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
    )

    skill = AgentSkill(
        id="security_evaluation",
        name="Security Threat Evaluation",
        description="Evaluates input for security threats like SQL injection and XSS",
        tags=["security", "threat-detection", "input-validation"],
        examples=["Evaluate this input for security threats"],
    )

    agent_card = AgentCard(
        name="Security Judge Agent",
        description="An agent that evaluates input for security threats",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        authentication=None,
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=capabilities,
        skills=[skill],
    )

    task_manager = JudgeTaskManager(judge_agent_call=call_judge_agent)

    return A2AServer(
        agent_card=agent_card,
        task_manager=task_manager,
        host=host,
        port=port,
    )


def create_mask_server(host="localhost", port=10003, call_mask_agent=None) -> A2AServer:
    """Create and return an A2A server for the masking agent."""
    if not call_mask_agent:
        raise ValueError("Mask agent callback function is required")

    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
    )

    skill = AgentSkill(
        id="data_masking",
        name="PII Data Masking",
        description="Masks personally identifiable information (PII) in text",
        tags=["privacy", "data-protection", "pii"],
        examples=["Mask the PII in this text"],
    )

    agent_card = AgentCard(
        name="Data Masking Agent",
        description="An agent that masks sensitive data in text",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        authentication=None,
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=capabilities,
        skills=[skill],
    )

    task_manager = MaskTaskManager(mask_agent_call=call_mask_agent)

    return A2AServer(
        agent_card=agent_card,
        task_manager=task_manager,
        host=host,
        port=port,
    )
