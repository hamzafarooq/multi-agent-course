import os
import uuid

from google.adk.agents import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from cs_agent.security.masker import mask_sensitive_data

MASK_MODEL = "gemini-2.5-flash"

MASK_INSTRUCTION = """You are a privacy expert that masks sensitive data.
    Follow these steps:
    1. Identify PII and sensitive information in the text
    2. Use the mask_text tool to protect sensitive data
    3. Return the masked version of the input in plain text, in readable format"""


def mask_text(text: str) -> dict:
    """Masks sensitive data like PII in text using Google Cloud DLP."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    masked_result = mask_sensitive_data(project_id, text)
    return {"masked_text": masked_result}


mask_tool = FunctionTool(func=mask_text)

mask_agent = LlmAgent(
    name="data_masker",
    model=MASK_MODEL,
    instruction=MASK_INSTRUCTION,
    description="An agent that masks sensitive data in text.",
    tools=[mask_tool],
)

mask_session_service = InMemorySessionService()
mask_runner = Runner(
    agent=mask_agent,
    app_name="privacy_app",
    session_service=mask_session_service,
)


async def call_mask_agent(text: str) -> str:
    """Run the masking agent on *text* and return the masked output."""
    session_id = f"mask_{uuid.uuid4()}"
    await mask_session_service.create_session(
        app_name="privacy_app",
        user_id="user_1",
        session_id=session_id,
    )

    content = types.Content(role="user", parts=[types.Part(text=text)])
    result_text = ""

    async for event in mask_runner.run_async(
        user_id="user_1",
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                result_text = event.content.parts[0].text
            break

    return result_text
