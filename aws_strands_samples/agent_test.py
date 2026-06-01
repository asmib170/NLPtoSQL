"""Test agent using strands-agents with calculator and current_time tools."""

from strands import Agent
from strands_tools import calculator, current_time

print("Strands is installed and imports are working!")

agent = Agent(
    system_prompt="You are a helpful assistant that provides concise responses. You also have some tools",
    model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    tools=[calculator, current_time]
)

response = agent("""
1. What is the current time?
2. What is 2456 * 982?
""")

print(response)
