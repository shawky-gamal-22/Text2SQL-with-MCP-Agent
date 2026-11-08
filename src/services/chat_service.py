import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from src.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, agent: Any) -> None:
        self._agent = agent

    async def stream_response(
        self,
        message: str,
        conversation_id: str | None = None,
    ) -> AsyncIterator[str]:
        conversation_id = ConversationService.resolve_conversation_id(conversation_id)
        config = ConversationService.checkpoint_config(conversation_id)

        yield self._event(
            "conversation",
            {"conversation_id": conversation_id},
        )

        try:
            stream = await self._agent.astream_events(
                {"messages": [{"role": "user", "content": message}]},
                config=config,
                version="v3",
            )

            async with stream:
                async for streamed_message in stream.messages:
                    async for token in streamed_message.text:
                        yield self._event(
                            "token",
                            {"conversation_id": conversation_id, "token": token},
                        )

                    async for tool_call in streamed_message.tool_calls:
                        yield self._event(
                            "tool_call",
                            {
                                "conversation_id": conversation_id,
                                "tool_call": str(tool_call),
                            },
                        )

                await stream.output()

            yield self._event(
                "done",
                {"conversation_id": conversation_id},
            )
        except Exception:
            logger.exception(
                "Chat stream failed for conversation %s",
                conversation_id,
            )
            yield self._event(
                "error",
                {
                    "conversation_id": conversation_id,
                    "error": "The assistant could not complete the request.",
                },
            )

    @staticmethod
    def _event(name: str, data: dict[str, str]) -> str:
        return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"