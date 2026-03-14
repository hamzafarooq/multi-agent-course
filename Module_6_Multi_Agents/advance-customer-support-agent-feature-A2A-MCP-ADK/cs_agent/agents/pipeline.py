from google.adk.agents import SequentialAgent

from cs_agent.agents.judge_agent import judge_agent
from cs_agent.agents.mask_agent import mask_agent

security_pipeline = SequentialAgent(
    name="security_pipeline",
    description="A pipeline that checks input for security threats and masks PII in the output.",
    sub_agents=[judge_agent, mask_agent],
)
