from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langgraph.checkpoint.redis import AsyncRedisSaver
from text2sql.llm_factory import LLMFactory
from text2sql.prompts import system_prompt
from config.settings import get_settings
from pathlib import Path
import asyncio
from fastmcp.client.transports import PythonStdioTransport
import os
import sys
from contextlib import asynccontextmanager


class AgentFactory:
    @staticmethod
    @asynccontextmanager
    async def create_agent():
        project_root = Path(__file__).resolve().parents[2]
        server_path = project_root / "mcp_server" / "server.py"
        settings = get_settings()

        transport = PythonStdioTransport(
            script_path=server_path,
            python_cmd=sys.executable,
            cwd=str(project_root),
            env={"PYTHONPATH": os.pathsep.join((str(project_root), str(project_root / "src")))},
        )

        REDIS_URL = settings.REDIS_URL
        memory = None
        async with AsyncRedisSaver.from_conn_string(REDIS_URL) as memory:

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
                checkpointer=memory,
            )
            yield agent


async def main():

    async with AgentFactory.create_agent() as agent:
        config = {"configurable": {"thread_id": "2"}}
        question = ["Do you remember my name"]
        for q in question:
            print("???????????????????????????????????")
            stream = await agent.astream_events(
                {"messages": [{"role": "user", "content": q}]},
                config=config,
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
