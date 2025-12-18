from ipykernel.kernelbase import Kernel
from pathlib import Path
import logging
import os
from pydantic import BaseModel
from pydantic_ai import (
    Agent,
    ModelRequest,
    UserPromptPart,
    ModelMessage,
    SystemPromptPart,
    ModelResponse,
    TextPart,
    FunctionToolset,
)

from pydantic_ai.models import infer_model
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.models.openai import OpenAIChatModel
from typing import Literal
from typing_extensions import TypedDict


def setup_kernel_logger(name, log_dir="~/.silik_logs"):
    log_dir = Path(log_dir).expanduser()

    if not os.path.isdir(log_dir):
        raise Exception(f"Please create a dir for kernel logs at {log_dir}")
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if not logger.handlers:
        fh = logging.FileHandler(log_dir / f"{name}.log", encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


class InferenceProviderConfig(BaseModel):
    name: str
    url: str


class AgentConfig(BaseModel):
    agent_name: str
    system_prompt: str
    model_name: str
    tools: list[str] | str | None = None
    provider: InferenceProviderConfig | None = None


class ChatMessage(TypedDict):
    """Format of messages sent to the browser."""

    role: Literal["user", "assistant"]
    uid: str
    content: str


class PydanticAIBaseKernel(Kernel):
    r"""
    Kernel wrapper for pydantic agents. It is meant to be subclassed.
    """

    implementation = "PydanticAI Base Agent Kernel"
    implementation_version = "1.0"
    language = "no-op"
    language_version = "0.1"
    language_info = {
        "name": "pydantic_ai_agent",
        "mimetype": "text/plain",
        "file_extension": ".txt",
    }
    banner = "Pydantic AI Base Kernel"

    def __init__(
        self,
        agent_config: AgentConfig | None = None,
        tools: list | None = None,
        toolsets: list[FunctionToolset] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        should_custom_log = os.environ.get("PYDANTIC_AI_KERNEL_LOG", "False")
        should_custom_log = (
            True if should_custom_log in ["True", "true", "1"] else False
        )

        if should_custom_log:
            logger = setup_kernel_logger(__name__)
            logger.debug("Started kernel and initalized logger")
            self.logger = logger
        else:
            self.logger = self.log

        if agent_config is None:
            self.logger.debug(
                "No agent config was found. Initialize kernel with one, or sublass it."
            )
            return
        self.agent = self.create_agent(agent_config, tools, toolsets)
        self.message_history: list[ModelMessage] = [
            ModelRequest(parts=[SystemPromptPart(content=agent_config.system_prompt)])
        ]
        self.all_messages_ids = []

    def create_agent(
        self,
        agent_config: AgentConfig,
        tools: list | None,
        toolsets: list[FunctionToolset] | None,
    ) -> Agent:
        self.logger.info(agent_config)
        if agent_config.provider is not None and agent_config.provider.name == "ollama":
            provider = OllamaProvider(base_url=agent_config.provider.url)
            model = OpenAIChatModel(agent_config.model_name, provider=provider)
        else:
            model = infer_model(agent_config.model_name)

        agent = Agent(
            model,
            output_type=str,
            tools=tools if tools is not None else [],
            toolsets=toolsets if toolsets is not None else [],
            system_prompt=agent_config.system_prompt,
        )
        self.logger.info("Created agent : %s", agent)
        return agent

    def add_message_to_history(self, messages: list):
        for each_message in messages:
            if each_message["uid"] in self.all_messages_ids:
                continue
            match each_message["role"]:
                case "user":
                    parsed_message = ModelRequest(
                        parts=[UserPromptPart(content=each_message["content"])]
                    )
                    self.message_history.append(parsed_message)
                    self.all_messages_ids.append(each_message["uid"])
                case "assistant":
                    parsed_message = ModelResponse(
                        parts=[TextPart(content=each_message["content"])]
                    )
                    self.message_history.append(parsed_message)
                    self.all_messages_ids.append(each_message["uid"])
                case _:
                    self.logger.debug(
                        f"Could not add message {each_message} to history"
                    )

    async def do_execute(  # pyright: ignore
        self,
        code,
        silent,
        store_history=True,
        user_expressions=None,
        allow_stdin=False,
    ):
        parent = self.get_parent()
        metadata = parent.get("metadata", {})
        self.logger.debug(f"metadata {metadata}")
        if isinstance(metadata, dict) and "message_history" in metadata:
            self.add_message_to_history(metadata["message_history"])
        self.logger.info(f"Message history {self.message_history}")
        # Process the metadata as needed

        agent_answer = await self.agent.run(code, message_history=self.message_history)

        content = agent_answer.output
        self.send_response(
            self.iopub_socket,
            "execute_result",
            {
                "execution_count": self.execution_count,
                "data": {"text/plain": content},
                "metadata": {},
            },
        )
        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }

    def do_shutdown(self, restart):
        return super().do_shutdown(restart)
