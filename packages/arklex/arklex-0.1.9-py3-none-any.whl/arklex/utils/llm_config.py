from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# List of supported language model providers
LLM_PROVIDERS: list[str] = [
    "openai",  # OpenAI's language models
    "google",  # Google's models
    "anthropic",  # Anthropic's Claude models
    "huggingface",  # HuggingFace's open-source models
]


class LLMConfig(BaseModel):
    llm_provider: str = Field(default="openai")
    model_type_or_path: str = Field(default="gpt-4o")


def get_huggingface_llm(model: str, **kwargs: object) -> any:
    """Initialize a HuggingFace language model.

    This function creates a HuggingFace language model instance using the specified model
    and configuration parameters. It sets up the model for text generation tasks.

    Args:
        model (str): The HuggingFace model identifier to use.
        **kwargs (object): Additional configuration parameters for the model.

    Returns:
        ChatHuggingFace: A configured HuggingFace chat model instance.

    Example:
        llm = get_huggingface_llm(
            model="gpt2",
            temperature=0.7,
            max_length=100
        )
    """
    from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

    llm: HuggingFaceEndpoint = HuggingFaceEndpoint(
        repo_id=model, task="text-generation", **kwargs
    )
    return ChatHuggingFace(llm=llm)


def load_llm(llm_config: LLMConfig) -> any:
    """Load a language model based on the configuration."""
    if llm_config.llm_provider == "openai":
        return ChatOpenAI(model=llm_config.model_type_or_path)
    elif llm_config.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=llm_config.model_type_or_path)
    elif llm_config.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=llm_config.model_type_or_path)
    elif llm_config.llm_provider == "huggingface":
        return get_huggingface_llm(model=llm_config.model_type_or_path)
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_config.llm_provider}")
