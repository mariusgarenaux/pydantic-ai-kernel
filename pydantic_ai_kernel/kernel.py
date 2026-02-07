from .agent_config import AgentConfig
from .command_parser import CommandParser, Command, CommandArgs

import traceback
import shlex
from ipykernel.kernelbase import Kernel
from pathlib import Path
import logging
import os
from uuid import uuid4
import yaml
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

from typing import Literal, Type
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


logger = setup_kernel_logger(__name__)


class ChatMessage(TypedDict):
    """Format of messages sent to the browser."""

    role: Literal["user", "assistant"]
    uid: str
    content: str


class PydanticAIBaseKernel(Kernel):
    """
    Kernel wrapper for pydantic agents. It is meant to be subclassed.
    """

    implementation = "PydanticAI Base Agent Kernel"
    implementation_version = "1.0"
    language = "no-op"
    language_version = "0.1"
    language_info = {
        "name": "pydantic_ai",
        "mimetype": "text/plain",
        "file_extension": ".txt",
    }
    banner = "Pydantic AI Base Kernel"

    def __init__(
        self,
        kernel_name: str = "pydantic_ai",
        agent_config: AgentConfig | None = None,
        tools: list | None = None,
        toolsets: list[FunctionToolset] | None = None,
        output_type: Type = str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if kernel_name == "pydantic_ai" and self.language_info["name"] != "pydantic_ai":
            raise Exception(
                "Specify parameter 'name' in all subclasses of PydanticAIBaseKernel."
            )
        self.kernel_name = kernel_name

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

        try:
            if agent_config is None:
                agent_config = self.load_config()
            self.agent = self.create_agent(agent_config, tools, toolsets, output_type)
            self.message_history: list[ModelMessage] = [
                ModelRequest(
                    parts=[SystemPromptPart(content=agent_config.system_prompt)]
                )
            ]
        except Exception as e:
            self.logger.debug(f"Could not load default config {e}.")
            self.agent = None

        self.all_messages_ids = []
        self.all_cmds = {
            "/system_prompt": Command(
                self.change_agent_config_handler,
                CommandParser(["prompt"]),
            ),
            "/load_config": Command(self.reload_config, CommandParser(["dir"])),
        }

    def reload_config(self, args):
        new_conf = self.load_config(config_dir=args.dir)
        agent = self.create_agent(new_conf)
        self.logger.debug(agent)
        self.agent = agent
        self.message_history = []
        return "Updated config file"

    def post_processing(self, content: str):
        """
        Abstract method that can be overwritten in order to implement
        post-processing on agent output.
        (validation, removing beginning of string, ...).
        """
        return content

    def load_config(self, config_dir: str | None = None) -> AgentConfig:
        """
        Try to load config file at ~/.jupyter/jupyter_<kernel_name>_config.yaml.
        Returns the validated config object, or raise an Error.

        Parameters :
        ---
            - config_dir (Optional[str]) : path to the config file. If None,
                is set to ~/.jupyter/jupyter_<kernel_name>_config.yaml

        Returns :
        ---
            AgentConfig pydantic BaseMode, validated
        """
        if config_dir is None:
            home = Path.home()
            dir = home / f".jupyter/jupyter_{self.kernel_name}_config.yaml"
        else:
            dir = config_dir
        try:
            with open(dir, "rt") as f:
                conf = yaml.safe_load(f)
            validated_conf = AgentConfig.model_validate(conf)
            return validated_conf
        except Exception as e:
            raise Exception(
                f"Could not load and validate config file for agent at {dir}."
            ) from e

    def create_agent(
        self,
        agent_config: AgentConfig,
        tools: list | None = None,
        toolsets: list[FunctionToolset] | None = None,
        output_type=str,
    ) -> Agent:
        try:
            model = agent_config.model.get_model
        except NotImplementedError as e:
            model = agent_config.model.model_name
            logger.warning(e)
        agent = Agent(
            model,
            output_type=output_type,
            system_prompt=agent_config.system_prompt,
            tools=tools if tools is not None else (),
            toolsets=toolsets,
            name=agent_config.agent_name,
        )

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

    def change_agent_config_handler(self, args):
        """
        Changes agent config directly by sending messages to kernel
        """
        new_agent = Agent(
            model=self.agent.model,
            system_prompt=args.prompt,
            output_type=self.agent.output_type,
            name=self.agent.name,
        )

        self.agent = new_agent
        self.message_history = []

    async def do_execute(  # pyright: ignore
        self,
        code,
        silent,
        store_history=True,
        user_expressions=None,
        allow_stdin=False,
    ):
        try:
            splitted_code = code.split(" ")
            cmd = splitted_code[0]
            self.logger.debug(f"Here cmd : {cmd}")
            if cmd in self.all_cmds:
                cmd_obj = self.all_cmds[cmd]
                splitted = shlex.split(code)
                self.logger.debug(f"shlex splitted {splitted}")
                args = cmd_obj.parser.parse(splitted[1:])
                self.logger.debug(f"command : {cmd} {args}, {cmd_obj.handler}")
                cmd_out = cmd_obj.handler(args)
                cmd_out = "" if cmd_out is None else cmd_out

                self.logger.debug(f"cmd out : {cmd_out}")
                self.send_response(
                    self.iopub_socket,
                    "execute_result",
                    {
                        "execution_count": self.execution_count,
                        "data": {"text/plain": cmd_out},
                    },
                )
                return {
                    "status": "ok",
                    "execution_count": self.execution_count,
                    "payload": [],
                    "user_expressions": {},
                }
            else:
                if self.agent is None:
                    self.send_response(
                        self.iopub_socket,
                        "error",
                        {
                            "ename": "",
                            "evalue": "",
                            "traceback": [
                                "Load config file before using the agent. Send `/load_config <config_dir>`. See https://github.com/mariusgarenaux/pydantic-ai-kernel to get config scheme."
                            ],
                        },
                    )
                    return {
                        "status": "error",
                        "execution_count": self.execution_count,
                        "payload": [],
                        "user_expressions": {},
                    }
                agent_answer = await self.agent.run(
                    code, message_history=self.message_history
                )

                content = str(agent_answer.output)
                content = self.post_processing(content)

                question_id = str(uuid4())
                answer_id = str(uuid4())
                new_messages = [
                    {
                        "role": "user",
                        "content": code,
                        "uid": question_id,
                    },
                    {
                        "role": "assistant",
                        "content": content,
                        "uid": answer_id,
                    },
                ]
                self.add_message_to_history(new_messages)
                self.send_response(
                    self.iopub_socket,
                    "execute_result",
                    {
                        "execution_count": self.execution_count,
                        "data": {"text/plain": content},
                        "metadata": {"new_messages_id": [question_id, answer_id]},
                    },
                )
                return {
                    "status": "ok",
                    "execution_count": self.execution_count,
                    "payload": [],
                    "user_expressions": {},
                }
        except Exception as e:
            self.send_response(
                self.iopub_socket,
                "error",
                {
                    "ename": "",
                    "evalue": "",
                    "traceback": traceback.format_exception(e),
                },
            )
            return {
                "status": "error",
                "execution_count": self.execution_count,
                "payload": [],
                "user_expressions": {},
            }

    def do_is_complete(self, code):
        if code.endswith(" "):
            return {"status": "incomplete", "indent": ""}
        return {"status": "unknown", "indent": ""}

    def complete_first_word(self, splitted_code: list[str], cursor_pos: int):
        first_word = splitted_code[0]
        all_matches = []
        for each_cmd in self.all_cmds:
            if len(each_cmd) < len(first_word):
                continue
            potential_match = each_cmd[: len(first_word)]
            self.logger.debug(f"potential match : {potential_match}, {each_cmd}")
            if potential_match == first_word:
                all_matches.append(each_cmd)
        return {
            # status should be 'ok' unless an exception was raised during the request,
            # in which case it should be 'error', along with the usual error message content
            # in other messages.
            "status": "ok",
            # The list of all matches to the completion request, such as
            # ['a.isalnum', 'a.isalpha'] for the above example.
            "matches": all_matches,
            # The range of text that should be replaced by the above matches when a completion is accepted.
            # typically cursor_end is the same as cursor_pos in the request.
            "cursor_start": cursor_pos - len(first_word),
            "cursor_end": cursor_pos,
            # Information that frontend plugins might use for extra display information about completions.
            "metadata": {},
        }

    def do_complete(self, code: str, cursor_pos: int):
        splitted = code.split(" ")
        self.logger.debug(f"do complete , splitted = {splitted}")
        if len(splitted) == 0:
            return {
                "status": "ok",
                "matches": [],
                "cursor_start": cursor_pos,
                "cursor_end": cursor_pos,
                "metadata": {},
            }
        if len(splitted) == 1:
            return self.complete_first_word(splitted, cursor_pos)
        if splitted[0] not in self.all_cmds:
            return {
                "status": "ok",
                "matches": [],
                "cursor_start": cursor_pos,
                "cursor_end": cursor_pos,
                "metadata": {},
            }

        return {
            # status should be 'ok' unless an exception was raised during the request,
            # in which case it should be 'error', along with the usual error message content
            # in other messages.
            "status": "ok",
            # The list of all matches to the completion request, such as
            # ['a.isalnum', 'a.isalpha'] for the above example.
            "matches": [],
            # The range of text that should be replaced by the above matches when a completion is accepted.
            # typically cursor_end is the same as cursor_pos in the request.
            "cursor_start": cursor_pos,
            "cursor_end": cursor_pos,
            # Information that frontend plugins might use for extra display information about completions.
            "metadata": {},
        }

    def do_shutdown(self, restart):
        return super().do_shutdown(restart)
