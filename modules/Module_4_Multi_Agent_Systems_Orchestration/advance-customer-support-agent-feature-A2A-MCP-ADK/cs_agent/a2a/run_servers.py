"""Launch the Judge and Mask A2A servers in background threads."""

import asyncio
import logging
import threading

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from cs_agent.agents.judge_agent import call_judge_agent
from cs_agent.agents.mask_agent import call_mask_agent
from cs_agent.a2a.factories import create_judge_server, create_mask_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _run_server(server):
    logger.info("Starting server on %s:%s", server.host, server.port)
    uvicorn.run(server.app, host=server.host, port=server.port)


def start_all_servers(
    judge_host="localhost",
    judge_port=10002,
    mask_host="localhost",
    mask_port=10003,
):
    """Create and start all A2A servers in daemon threads.

    Returns a list of the started Thread objects.
    """
    judge_server = create_judge_server(
        host=judge_host, port=judge_port, call_judge_agent=call_judge_agent
    )
    mask_server = create_mask_server(
        host=mask_host, port=mask_port, call_mask_agent=call_mask_agent
    )

    threads = []
    for server in [judge_server, mask_server]:
        t = threading.Thread(target=_run_server, args=(server,), daemon=True)
        t.start()
        threads.append(t)

    logger.info("All A2A servers started (Judge :%s, Mask :%s)", judge_port, mask_port)
    return threads


def main():
    threads = start_all_servers()
    logger.info("Press Ctrl+C to stop.")
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")


if __name__ == "__main__":
    main()
