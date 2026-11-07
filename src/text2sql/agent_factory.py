from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from text2sql.llm_factory import LLMFactory
from text2sql.prompts import system_prompt
from config.settings import get_settings
from pathlib import Path
import asyncio
from fastmcp.client.transports import PythonStdioTransport
import sys


class AgentFactory:
    @staticmethod
    async def create_agent():
        project_root = Path(__file__).resolve().parents[2]
        server_path = project_root / "mcp_server" / "server.py"

        transport = PythonStdioTransport(
            script_path=server_path,
            python_cmd=sys.executable,
            cwd=str(project_root),
            env={"PYTHONPATH": f"{project_root};{project_root / 'src'}"},
        )

        settings = get_settings()
        llm_type = settings.llm_type
        kwargs = {
            "model_name": settings.CHAT_MODEL_NAME,
            "max_retries": settings.max_retries,
            "temperature": settings.temperature,
            "api_key": settings.GROQ_API_KEY,
        }
        llm = LLMFactory.create_llm(model_type=llm_type, **kwargs)

        adapter = MCPAdapter(transport)

        tools = await adapter.list_tools()

        agent = create_agent(
            model=llm,
            system_prompt=system_prompt,
            tools=tools,
        )
        return agent


async def main():
    agent = await AgentFactory.create_agent()
    question = "Which genre on average has the longest tracks?"

    stream = await agent.astream_events(
        {"messages": [{"role": "user", "content": question}]},
        version="v3",
    )

    async with stream:
        async for message in stream.messages:
            async for token in message.text:
                print(token, end="", flush=True)

            async for tool_call in message.tool_calls:
                print(f"\nTool call: {tool_call}")

        final_state = await stream.output()

    print()


if __name__ == "__main__":
    asyncio.run(main())
