import warnings
warnings.filterwarnings("ignore")
# Robustly silence library DeprecationWarnings: the google-adk import chain resets
# the warnings filter (defeating filterwarnings/PYTHONWARNINGS), but overriding
# showwarning drops them at the sink. Done in-process so we never have to filter
# stderr at the shell level — that breaks the interactive input() prompt.
warnings.showwarning = lambda *a, **k: None

import asyncio
import json
import logging
import os
import sys
from getpass import getpass

logging.getLogger().setLevel(logging.ERROR)

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
from telemetry import init_telemetry
from openinference.semconv.trace import SpanAttributes

logger = logging.getLogger(__name__)

load_dotenv()
tracer = init_telemetry()

A2A_JUDGE_HOST = os.getenv("A2A_JUDGE_HOST", "localhost")
A2A_JUDGE_PORT = int(os.getenv("A2A_JUDGE_PORT", "10002"))
A2A_MASK_HOST = os.getenv("A2A_MASK_HOST", "localhost")
A2A_MASK_PORT = int(os.getenv("A2A_MASK_PORT", "10003"))

# Print each MCP tool call + result inline so the tool-use loop is visible during
# a request (great for teaching/demos). Set CS_SHOW_TOOL_CALLS=0 to silence.
SHOW_TOOL_CALLS = os.getenv("CS_SHOW_TOOL_CALLS", "1") == "1"


def _fmt_tool_args(args) -> str:
    """Render tool args as name=value pairs for inline logging."""
    if not args:
        return ""
    try:
        return ", ".join(f"{k}={v!r}" for k, v in dict(args).items())
    except Exception:
        return str(args)

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
    with tracer.start_as_current_span("security.validate_input") as span:
        span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
        span.set_attribute(SpanAttributes.INPUT_VALUE, user_input)

        # --- Layer 1: Input sanitization (local) ---
        with tracer.start_as_current_span("security.sanitize") as san_span:
            san_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
            san_span.set_attribute(SpanAttributes.INPUT_VALUE, user_input)
            try:
                user_input = sanitize_input(user_input)
                san_span.set_attribute(SpanAttributes.OUTPUT_VALUE, "passed")
            except ValueError as exc:
                san_span.set_attribute(SpanAttributes.OUTPUT_VALUE, f"blocked: {exc}")
                print(f"\nInput rejected: {exc}")
                print("Please rephrase your question.\n")
                return False

        # --- Layer 2: Security Judge via A2A protocol ---
        with tracer.start_as_current_span("security.a2a_judge") as judge_span:
            judge_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
            judge_span.set_attribute(SpanAttributes.INPUT_VALUE, user_input)
            try:
                verdict = await call_a2a_agent(
                    query=user_input, host=A2A_JUDGE_HOST, port=A2A_JUDGE_PORT
                )
                blocked = "BLOCKED" in verdict.upper()
                judge_span.set_attribute(SpanAttributes.OUTPUT_VALUE, verdict[:200])
                if blocked:
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, "blocked")
                    print("\nSecurity Alert: Your input was flagged by the Security Judge agent.")
                    print("Please rephrase your question in a safe manner.\n")
                    return False
            except Exception as exc:
                judge_span.set_attribute(SpanAttributes.OUTPUT_VALUE, f"error: {exc}")
                logger.error("Judge A2A agent call failed: %s", exc)
                print("\nError: Could not reach the Security Judge A2A agent.")
                print("Ensure A2A servers are running: python -m cs_agent.a2a.run_servers\n")
                return False

        span.set_attribute(SpanAttributes.OUTPUT_VALUE, "passed")
        return True


async def _mask_response(text: str) -> str:
    """Apply PII masking via the Mask A2A agent."""
    with tracer.start_as_current_span("security.a2a_mask") as span:
        span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
        span.set_attribute(SpanAttributes.INPUT_VALUE, text[:500])
        try:
            masked = await call_a2a_agent(
                query=text, host=A2A_MASK_HOST, port=A2A_MASK_PORT
            )
            if not masked:
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, text[:500])
                return text
            lower_masked = masked.lower()
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, lower_masked[:500])
            return lower_masked
        except Exception as exc:
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, f"mask_skipped: {exc}")
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

        with tracer.start_as_current_span("agent.turn") as turn_span:
            turn_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "CHAIN")
            turn_span.set_attribute(SpanAttributes.INPUT_VALUE, user_input)
            turn_span.set_attribute("user.id", USER_ID)

            if not await validate_input(user_input):
                turn_span.set_attribute("turn.blocked", True)
                turn_span.set_attribute("turn.block_reason", "security_validation")
                turn_span.set_attribute(SpanAttributes.OUTPUT_VALUE, "BLOCKED: security_validation")
                continue

            with tracer.start_as_current_span("guardrail.check") as g_span:
                g_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
                g_span.set_attribute(SpanAttributes.INPUT_VALUE, user_input)
                passed = await _passes_guardrail(
                    user_input=user_input, runner=guardrail_runner, user_id=USER_ID
                )
                g_span.set_attribute("guardrail.passed", passed)
                g_span.set_attribute(SpanAttributes.OUTPUT_VALUE, "safe" if passed else "unsafe")

            if not passed:
                turn_span.set_attribute("turn.blocked", True)
                turn_span.set_attribute("turn.block_reason", "guardrail")
                turn_span.set_attribute(SpanAttributes.OUTPUT_VALUE, "BLOCKED: guardrail")
                print(
                    "\nI’m not able to help with that request. "
                    "Please ask a safe, customer-support–related question instead.\n"
                )
                continue

            # Show a short, context-aware loading message before calling the agent.
            await _show_loading(_loading_label_for_request(user_input))

            messages.append({"role": "user", "content": user_input})
            content = types.Content(role="user", parts=[types.Part(text=user_input)])

            tool_calls_log = []
            tool_results_log = []

            response = runner.run(
                user_id=USER_ID, session_id=f"session_{USER_ID}", new_message=content
            )

            for event in response:
                # Capture tool calls for observability
                for fc in (event.get_function_calls() or []):
                    tool_calls_log.append({"name": fc.name, "args": fc.args})
                    if SHOW_TOOL_CALLS:
                        print(f"  \033[2m[tool] → {fc.name}({_fmt_tool_args(fc.args)})\033[0m")

                for fr in (event.get_function_responses() or []):
                    resp_str = json.dumps(fr.response) if isinstance(fr.response, dict) else str(fr.response)
                    tool_results_log.append({"name": fr.name, "response": resp_str[:500]})
                    if SHOW_TOOL_CALLS:
                        print(f"  \033[2m[tool] ← {fr.name}: {resp_str[:300]}\033[0m")
                    with tracer.start_as_current_span(f"tool.{fr.name}") as tc_span:
                        tc_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "TOOL")
                        tc_span.set_attribute(SpanAttributes.TOOL_NAME, fr.name)
                        matching_call = next((c for c in tool_calls_log if c["name"] == fr.name), {})
                        tc_span.set_attribute(SpanAttributes.INPUT_VALUE, json.dumps(matching_call.get("args", {})))
                        tc_span.set_attribute(SpanAttributes.OUTPUT_VALUE, resp_str[:500])

                if event.is_final_response() and event.content:
                    raw_text = event.content.parts[0].text
                    masked_text = await _mask_response(raw_text)

                    turn_span.set_attribute(SpanAttributes.OUTPUT_VALUE, masked_text)
                    if tool_calls_log:
                        turn_span.set_attribute("llm.tool_calls", json.dumps(tool_calls_log))
                    if tool_results_log:
                        turn_span.set_attribute("llm.tool_results", json.dumps(tool_results_log))

                    usage = event.usage_metadata
                    if usage:
                        prompt_tokens = usage.prompt_token_count or 0
                        completion_tokens = usage.candidates_token_count or 0
                        thinking_tokens = usage.thoughts_token_count or 0
                        total_tokens = usage.total_token_count or 0
                        turn_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_PROMPT, prompt_tokens)
                        turn_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, completion_tokens)
                        turn_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_TOTAL, total_tokens)
                        turn_span.set_attribute("llm.token_count.thinking", thinking_tokens)
                        # Gemini 2.5 Flash pricing: $0.075/1M input, $0.30/1M output
                        cost_prompt = (prompt_tokens * 0.075) / 1_000_000
                        cost_completion = (completion_tokens * 0.30) / 1_000_000
                        turn_span.set_attribute(SpanAttributes.LLM_COST_PROMPT, cost_prompt)
                        turn_span.set_attribute(SpanAttributes.LLM_COST_COMPLETION, cost_completion)
                        turn_span.set_attribute(SpanAttributes.LLM_COST_TOTAL, cost_prompt + cost_completion)

                    print("Agent: ", masked_text)
                    messages.append({"role": "assistant", "content": masked_text})

    save_memory(messages, USER_ID)


if __name__ == "__main__":
    asyncio.run(main())
