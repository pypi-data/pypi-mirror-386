from functools import lru_cache

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI


@lru_cache(maxsize=8)
def load_chat_model(
    fully_specified_name: str, temperature: float = 1.0, tags: list[str] | None = None, thinking: bool = True
) -> BaseChatModel:
    """Load a chat model from a fully specified name.
    Args:
        fully_specified_name (str): String in the format 'provider/model'.
    """
    fully_specified_name = fully_specified_name.replace("/", ":")
    provider, model = fully_specified_name.split(":", maxsplit=1)
    if provider == "anthropic":
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            thinking={"type": "enabled", "budget_tokens": 2048} if thinking else None,
            max_tokens=4096,
            tags=tags,
            stream_usage=True,
        )  # pyright: ignore[reportCallIssue]
    elif provider == "azure":
        return AzureChatOpenAI(
            model=model,
            api_version="2024-12-01-preview",
            azure_deployment=model,
            temperature=temperature,
            tags=tags,
            stream_usage=True,
        )
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


if __name__ == "__main__":
    from loguru import logger

    models_to_test = [
        "azure/gpt-5-chat",
        "anthropic/claude-4-sonnet-20250514",
        "gemini/gemini-2.5-pro",
    ]
    for model in models_to_test:
        llm = load_chat_model(model)
        logger.info(llm.invoke("Hi!"))
