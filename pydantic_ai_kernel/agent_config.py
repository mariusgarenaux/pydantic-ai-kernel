from pydantic_ai import UserError
from pydantic_ai.models import infer_model, Model
from pydantic_ai.providers import infer_provider_class, Provider
from typing import Annotated, Any, Literal, Optional, Dict
from pydantic import BaseModel, Field, field_validator
import json
import os

AllModelKind = Literal[
    "test",
    "openai",
    "azure",
    "deepseek",
    "fireworks",
    "github",
    "grok",
    "heroku",
    "moonshotai",
    "ollama",
    "together",
    "vercel",
    "litellm",
    "nebius",
    "ovhcloud",
    "alibaba",
    "openai-chat",
    "openai-responses",
    "google-gla",
    "google-vertex",
    "google",
    "groq",
    "cohere",
    "mistral",
    "openrouter",
    "anthropic",
    "bedrock",
    "huggingface",
    "cerebras",
]


def infer_model_type(  # noqa: C901
    model_kind: str,
) -> type[Model]:
    """Infer the model type from the name.
    Function extracted and modified from pydantic-ai `infer_model`.

    Args:
        model_kind:
            Kind of model to instantiate. Use the string "test" to instantiate TestModel.
    """
    if model_kind == "test":
        from pydantic_ai.models.test import TestModel

        return TestModel

    if model_kind in (
        "openai",
        "azure",
        "deepseek",
        "fireworks",
        "github",
        "grok",
        "heroku",
        "moonshotai",
        "ollama",
        "together",
        "vercel",
        "litellm",
        "nebius",
        "ovhcloud",
        "alibaba",
    ):
        model_kind = "openai-chat"
    elif model_kind in ("google-gla", "google-vertex"):
        model_kind = "google"

    if model_kind == "openai-chat":
        from pydantic_ai.models.openai import OpenAIChatModel

        return OpenAIChatModel
    elif model_kind == "openai-responses":
        from pydantic_ai.models.openai import OpenAIResponsesModel

        return OpenAIResponsesModel
    elif model_kind == "google":
        from pydantic_ai.models.google import GoogleModel

        return GoogleModel
    elif model_kind == "groq":
        from pydantic_ai.models.groq import GroqModel

        return GroqModel
    elif model_kind == "cohere":
        from pydantic_ai.models.cohere import CohereModel

        return CohereModel
    elif model_kind == "mistral":
        from pydantic_ai.models.mistral import MistralModel

        return MistralModel
    elif model_kind == "openrouter":
        from pydantic_ai.models.openrouter import OpenRouterModel

        return OpenRouterModel
    elif model_kind == "anthropic":
        from pydantic_ai.models.anthropic import AnthropicModel

        return AnthropicModel
    elif model_kind == "bedrock":
        from pydantic_ai.models.bedrock import BedrockConverseModel

        return BedrockConverseModel
    elif model_kind == "huggingface":
        from pydantic_ai.models.huggingface import HuggingFaceModel

        return HuggingFaceModel
    elif model_kind == "cerebras":
        from pydantic_ai.models.cerebras import CerebrasModel

        return CerebrasModel
    else:
        raise UserError(f"Unknown model: {model_kind}")  # pragma: no cover


class ModelProviderConfig(BaseModel):
    name: Annotated[
        str,
        Field(
            description="Name of the inference provider. The complete list is the one from pydantic-ai. https://ai.pydantic.dev/api/providers/",
            examples=[
                "ollama",
                "litellm",
                "anthropic",
                "nebius",
                "alibaba",
                "ovhcloud",
            ],
        ),
    ]
    params: Annotated[
        dict,
        Field(
            description="The parameters that will be given to pydantic-ai Provider class. Depends on provider name. Go to : https://ai.pydantic.dev/models/overview/",
            examples=[{"base_url": "http://localhost:11434/v1"}],
        ),
    ]

    @property
    def get_provider(self) -> Provider[Any]:
        ProviderConstructor = infer_provider_class(self.name)
        return ProviderConstructor(**self.params)


class ModelConfig(BaseModel):
    """
    Describe a model and its inference provider. Is given to pydantic-ai
    agent.
    """

    model_type: AllModelKind | None = None
    model_name: Annotated[
        str,
        Field(
            description="""Following pydantic-ai implementation, there are two ways
 to write model name :
    - <provider_name>:<model_name>, example 'ollama:qwen3:1.7b
    - <model_name>
    
In the first one, you CAN provide additionnal informations on the provider within
the field 'provider' below. They will **erase** the ones infered by pydantic-ai.
A wide range of values is possible here, and you can refer to pydantic-ai documentation :
https://ai.pydantic.dev/models/overview/

In the second one, you MUST provide additionnal informations on the provider within
the field 'provider' below.""",
            examples=["ollama:qwen3:1.7b", "qwen3.1:1.7b"],
        ),
    ]
    model_settings: Annotated[
        dict | None,
        Field(
            description="Settings for the model. Depends on model and inference provider. See https://ai.pydantic.dev/api/settings/#pydantic_ai.settings.ModelSettings",
            default=None,
        ),
    ]
    model_provider: Annotated[
        ModelProviderConfig | None,
        Field(
            description="Description of the inference provider. When specified, inferred information about the provider from model_name will be erased.",
            default=None,
        ),
    ]

    @property
    def get_model(self) -> Model | None:
        if self.model_type is None:
            try:
                return infer_model(self.model_name)
            except Exception as e:
                raise Exception(
                    f"Could not access model. See error above or consider adding at least information about the model type in the configuration file. Model types are : {AllModelKind}."
                ) from e
        if self.model_provider is None:
            try:
                return infer_model(self.model_name)
            except Exception as e:
                raise Exception(
                    "Could not access model. See error above or consider adding at least a model provider in configuration file"
                ) from e

        provider = self.model_provider.get_provider
        ModelConstructor = infer_model_type(self.model_type)
        return ModelConstructor(self.model_name, provider=provider)  # pyright: ignore


class AgentConfig(BaseModel):
    agent_name: Annotated[
        str,
        Field(
            description="The name of the agent within the application - different from model name.",
            examples=["my-agent", "summarizer", "image-generator"],
        ),
    ]
    system_prompt: Annotated[
        str,
        Field(
            description="The system prompt for this agent, or a path towards a text file containing system prompt.",
            examples=[
                "You are a nice agent who answers nicely to requests of the user",
                "You are a specialist in cooking and are always willing to provide informations on new cooking recipees.",
                "/Users/mgg/Documents/system_prompt.txt",
                "/Users/mgg/Documents/system_prompt.md",
            ],
        ),
    ]
    model: ModelConfig
    mcp_servers: Annotated[
        Optional[Dict[str, Any]],
        Field(
            description="A dictionnary of MCP server configuration to connect to. Keys are MCP server names.",
            examples=[
                {
                    "time_mcp_server": {
                        "command": "uvx",
                        "args": ["mcp-run-python", "stdio"],
                    },
                    "weather_server": {"command": "python", "args": ["mcp_server.py"]},
                },
                {
                    "python-runner": {
                        "command": "uv",
                        "args": ["run", "mcp-run-python", "stdio"],
                    },
                    "weather": {"command": "python", "args": ["mcp_server.py"]},
                    "weather-api": {"url": "http://localhost:3001/sse"},
                    "calculator": {"url": "http://localhost:8000/mcp"},
                },
            ],
        ),
    ] = None
    mcp_servers_user_approval: Annotated[
        Optional[Dict[str, bool | dict]],
        Field(
            description="For each MCP server, information about whether the tool requires user approval or not. Can be either a boolean : True = All tools in the MCP server requires user validation (False = all tools **don't** requires validation). Or can be a dict where keys are tool names, and values boolean. When not specified, a tool needs user validation by default.",
            examples=[
                {
                    "python-runner": True,
                    "weather-api": {"get_weather": True, "authenticate_to_api": False},
                    "calculator": False,
                }
            ],
        ),
    ] = None
    display_thinking: Annotated[
        bool,
        Field(
            description="Whether or not to display thinking text of the model. Default to true."
        ),
    ] = True
    formatter: Annotated[
        str,
        Field(
            description="Output formatter for magics (text, terminal, md, json).",
            examples=["text", "terminal", "md", "json"],
        ),
    ] = "terminal"
    use_widget: Annotated[
        bool,
        Field(
            description="Whether to use ipywidget in frontend for enhanced displaying"
        ),
    ] = False

    @field_validator("system_prompt", mode="after")
    @classmethod
    def load_system_prompt(cls, value: str):
        """
        If system prompt argument is a path, loads it.
        Else, does nothing.
        """
        if os.path.isfile(value):
            with open(value, "rt") as f:
                o = f.read()
            return o
        return value

    @field_validator("display_thinking", mode="after")
    @classmethod
    def validate_display_thinking(cls, value):
        # env variable overrides config value
        if os.getenv("PYDANTIC_AI_KERNEL_DISPLAY_THINKING", False):
            return True
        return value

    @field_validator("formatter", mode="after")
    @classmethod
    def validate_formatter(cls, value):
        # env variable overrides config value; fallback to default if not set
        env = os.getenv("PYDANTIC_AI_KERNEL_FORMATTER", False)
        if env:
            return env
        return value


if __name__ == "__main__":
    import json

    with open("config_scheme.json", "wt") as f:
        json.dump(AgentConfig.model_json_schema(), f)
