from langchain.agents import create_agent
from text2sql.llm_factory import LLMFactory
from text2sql.prompts import system_prompt
from text2sql.tools import (
    sql_db_list_tables,
    sql_db_schema,
    sql_db_query,
    sql_db_query_checker,
)
from config.settings import get_settings


class AgentFactory:
    @staticmethod
    def create_agent():
        settings = get_settings()
        llm_type = settings.llm_type
        kwargs = {
            "model_name": settings.CHAT_MODEL_NAME,
            "max_retries": settings.max_retries,
            "temperature": settings.temperature,
            "api_key": settings.GROQ_API_KEY,
        }
        llm = LLMFactory.create_llm(model_type=llm_type, **kwargs)

        agent = create_agent(
            model=llm,
            system_prompt=system_prompt,
            tools=[
                sql_db_list_tables,
                sql_db_schema,
                sql_db_query,
                sql_db_query_checker,
            ],
        )
        return agent


if __name__ == "__main__":
    agent = AgentFactory.create_agent()
    question = "Which genre on average has the longest tracks?"

    stream = agent.stream_events(
        {"messages": [{"role": "user", "content": question}]},
        version="v3",
    )
    for kind, item in stream.interleave("messages", "tool_calls"):
        if kind == "messages":
            for token in item.text:
                print(token, end="", flush=True)
        elif kind == "tool_calls":
            print(f"\nTool call: {item.tool_name}({item.input})")
            for delta in item.output_deltas:
                print(delta, end="", flush=True)
            print(f"\nTool result: {item.output}")

    final_state = stream.output
