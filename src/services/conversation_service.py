from uuid import uuid4


class ConversationService:
    @staticmethod
    def resolve_conversation_id(conversation_id: str | None) -> str:
        return conversation_id or str(uuid4())

    @staticmethod
    def checkpoint_config(conversation_id: str) -> dict[str, dict[str, str]]:
        return {"configurable": {"thread_id": conversation_id}}