import asyncio
import json
import logging
import os
import sys
from getpass import getpass

# Ensure both the cs_agent/ dir (for memory, prompts, greet) and the
# project root (for cs_agent.* packages) are importable.
_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import aiohttp
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from toolbox_core import ToolboxSyncClient
from google.adk.sessions import InMemorySessionService
from dotenv import load_dotenv
from tabulate import tabulate

from memory import search_memory, save_memory
from prompts import SQL_PROMPT_INSTRUCTION, GUARDRAIL_PROMPT_INSTRUCTION
from greet import authenticate_user, display_users, get_user_actions

from cs_agent.security.sanitizer import sanitize_input
from cs_agent.a2a.client import call_a2a_agent

logger = logging.getLogger(__name__)

load_dotenv()

A2A_JUDGE_HOST = os.getenv("A2A_JUDGE_HOST", "localhost")
A2A_JUDGE_PORT = int(os.getenv("A2A_JUDGE_PORT", "10002"))
A2A_MASK_HOST = os.getenv("A2A_MASK_HOST", "localhost")
A2A_MASK_PORT = int(os.getenv("A2A_MASK_PORT", "10003"))

toolbox_client = ToolboxSyncClient(
    url="http://127.0.0.1:5000"
)

database_tools = toolbox_client.load_toolset("cs_agent_tools")


async def _check_a2a_servers() -> bool:
    """Verify that the required A2A servers are reachable at startup."""
    servers = [
        ("Security Judge", A2A_JUDGE_HOST, A2A_JUDGE_PORT),
        ("Data Masker", A2A_MASK_HOST, A2A_MASK_PORT),
    ]
    all_ok = True
    for name, host, port in servers:
        url = f"http://{host}:{port}/.well-known/agent.json"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        card = await resp.json()
                        print(f"  [OK] {name} agent connected  ({card.get('name', 'unknown')})")
                    else:
                        print(f"  [FAIL] {name} agent returned HTTP {resp.status}")
                        all_ok = False
        except Exception as exc:
            print(f"  [FAIL] {name} agent at {host}:{port} -- {exc}")
            all_ok = False
    return all_ok


async def validate_input(user_input: str) -> bool:
    """Two-layer input validation using A2A protocol.

    Layer 1 -- sanitize_input(): character whitelist, length check, optional Model Armor API.
    Layer 2 -- Judge A2A agent: LLM-powered security evaluation with 100+ regex patterns.

    Returns True if all layers pass, False if any layer blocks.
    """
    # --- Layer 1: Input sanitization (local) ---
    try:
        user_input = sanitize_input(user_input)
    except ValueError as exc:
        print(f"\nInput rejected: {exc}")
        print("Please rephrase your question.\n")
        return False

    # --- Layer 2: Security Judge via A2A protocol ---
    try:
        verdict = await call_a2a_agent(
            query=user_input, host=A2A_JUDGE_HOST, port=A2A_JUDGE_PORT
        )
        if "BLOCKED" in verdict.upper():
            print("\nSecurity Alert: Your input was flagged by the Security Judge agent.")
            print("Please rephrase your question in a safe manner.\n")
            return False
    except Exception as exc:
        logger.error("Judge A2A agent call failed: %s", exc)
        print("\nError: Could not reach the Security Judge A2A agent.")
        print("Ensure A2A servers are running: python -m cs_agent.a2a.run_servers\n")
        return False

    return True


async def _mask_response(text: str) -> str:
    """Apply PII masking via the Mask A2A agent."""
    try:
        masked = await call_a2a_agent(
            query=text, host=A2A_MASK_HOST, port=A2A_MASK_PORT
        )
        if not masked:
            return text
        lower_masked = masked.lower()
        

        return lower_masked
    except Exception as exc:
        logger.warning("Mask A2A agent unreachable, returning raw text: %s", exc)
        return text


async def _passes_guardrail(
    user_input: str,
    runner: Runner,
    user_id: str,
) -> bool:
    """Run topical and safety guardrails using GUARDRAIL_PROMPT_INSTRUCTION.

    The guardrail agent returns a JSON object with `decision` and `reasoning`.
    If anything goes wrong, default to allowing the input.
    """
    try:
        content = types.Content(role="user", parts=[types.Part(text=user_input)])
        response = runner.run(
            user_id=user_id, session_id=f"guardrail_{user_id}", new_message=content
        )
        final_text = None
        for event in response:
            if event.is_final_response() and event.content:
                final_text = event.content.parts[0].text
        if not final_text:
            return True

        # Some models may occasionally return plain text instead of JSON. In that
        # case, treat the request as safe without raising noisy errors.
        stripped = final_text.lstrip()
        if not stripped or stripped[0] not in ("{", "["):
            return True

        decision_payload = json.loads(final_text)
        decision = str(decision_payload.get("decision", "safe")).lower()
        return decision == "safe"
    except Exception as exc:
        # Swallow JSON/guardrail errors silently and allow the request to
        # proceed so the user does not see internal failures.
        return True


async def _show_loading(message: str, dots: int = 3, delay: float = 0.4) -> None:
    """Display a simple CLI loading indicator with a base message."""
    print(f"\n{message}", end="", flush=True)
    for _ in range(dots):
        await asyncio.sleep(delay)
        print(".", end="", flush=True)
    print()


def _loading_label_for_request(user_input: str) -> str:
    """Pick a loading label based on the user's request text."""
    text = user_input.lower()
    if "order history" in text or "all my orders" in text or "orders for" in text:
        return "Loading order history"
    if "status" in text or "track" in text:
        return "Fetching order status"
    if "address" in text:
        return "Updating delivery address"
    if "return" in text or "refund" in text:
        return "Processing return request"
    return "Processing your request"


def _print_main_menu() -> None:
    """Display a quick menu of what the agent can do."""
    print("\nYou can ask me to:")
    print("  1. Check the status of a specific order (e.g., \"What's the status of order 5?\").")
    print("  2. Show your order history (e.g., \"Show all my past orders.\").")
    print("  3. Request to cancel or return an order.")
    print("  4. Request to update your delivery address or contact details.")


async def main():
    print("=" * 80)
    print("Welcome to the Customer Support Assistant")
    print("=" * 80)

    print("\nConnecting to A2A agents...")
    if not await _check_a2a_servers():
        print("\nFATAL: A2A servers are not running.")
        print("Start them first:  python -m cs_agent.a2a.run_servers")
        print("Then restart this CLI.")
        return


    display_users()

    print("=" * 80)
    email = input("Enter your email: ").strip()
    password = getpass("Enter your password: ").strip()

    # Multi-step startup loader to make the experience feel polished.
    await _show_loading("[1/4] Authenticating user")

    user_context = authenticate_user(email=email, password=password)
    if not user_context:
        print("Not authorized. Exiting demo.")
        return

    USER_ID = user_context["email"]

    # Continue the loader sequence now that we know who the user is.
    await _show_loading("[2/4] Loading user memory")
    await _show_loading("[3/4] Loading current orders")
    await _show_loading("[4/4] Loading previous actions")

    # Fetch and display action log for this user
    actions = get_user_actions(USER_ID)
    if actions:
        print("\n--- Your action history ---")
        rows = [
            (a["id"], a["timestamp"], a["action_type"], str(a["parameters"])[:60] + ("..." if len(str(a["parameters"])) > 60 else ""))
            for a in actions
        ]
        print(tabulate(rows, headers=["ID", "Time", "Action", "Details"], tablefmt="simple"))
        print()
    else:
        print("\nNo previous actions recorded.\n")

    if user_context['is_premium_customer']:
        print(f"Agent: Hello {user_context['full_name']}! Welcome to the Customer Support Assistant. How can I help you today? You are a premium customer and have {user_context['total_items_purchased']} items purchased.")
    else:
        print( f"Agent: Hello {user_context['full_name']}! Welcome to the Customer Support Assistant. How can I help you today?")
    _print_main_menu()

    IMPROVED_SQL_PROMPT_INSTRUCTION = SQL_PROMPT_INSTRUCTION.format(USER_ID=USER_ID)

    root_agent = LlmAgent(
        model="gemini-2.5-flash",
        name="customer_support_assistant",
        description=(
            "An expert customer support agent helping users with order-related questions and requests. "
            "Provides fast, clear, and friendly assistance with memory of past interactions."
        ),
        instruction=IMPROVED_SQL_PROMPT_INSTRUCTION,
        tools=[*database_tools, search_memory],
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name="agents", session_service=session_service)

    guardrail_agent = LlmAgent(
        model="gemini-2.5-flash",
        name="guardrail_agent",
        description=(
            "A safety and topical alignment guardrail that decides whether a "
            "user request is safe and in-scope for the customer support agent."
        ),
        instruction=GUARDRAIL_PROMPT_INSTRUCTION,
    )
    guardrail_runner = Runner(
        agent=guardrail_agent, app_name="guardrail", session_service=session_service
    )

    await session_service.create_session(
        app_name="agents", user_id=USER_ID, session_id=f"session_{USER_ID}"
    )
    await session_service.create_session(
        app_name="guardrail", user_id=USER_ID, session_id=f"guardrail_{USER_ID}"
    )

    messages = []

    while True:
        print("=" * 80)
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye", "q"]:
            break

        if not await validate_input(user_input):
            continue

        if not await _passes_guardrail(
            user_input=user_input, runner=guardrail_runner, user_id=USER_ID
        ):
            print(
                "\nI’m not able to help with that request. "
                "Please ask a safe, customer-support–related question instead.\n"
            )
            continue

        # Show a short, context-aware loading message before calling the agent.
        await _show_loading(_loading_label_for_request(user_input))

        messages.append({"role": "user", "content": user_input})
        content = types.Content(role="user", parts=[types.Part(text=user_input)])
        response = runner.run(
            user_id=USER_ID, session_id=f"session_{USER_ID}", new_message=content
        )

        for event in response:
            if event.is_final_response() and event.content:
                raw_text = event.content.parts[0].text
                masked_text = await _mask_response(raw_text)
                print("Agent: ", masked_text)
                messages.append({"role": "assistant", "content": masked_text})

    save_memory(messages, USER_ID)


if __name__ == "__main__":
    asyncio.run(main())
