from langchain_groq import ChatGroq


class LLMFactory:
    @staticmethod
    def create_llm(model_type: str, **kwargs):
        if model_type == "groq":
            return ChatGroq(**kwargs)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
