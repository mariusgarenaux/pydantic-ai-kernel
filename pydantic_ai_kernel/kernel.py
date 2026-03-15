# Internal Imports
from .agent_config import AgentConfig
from .utils import prompt_user_approval

# Base python dependencies
import importlib
import glob
import sys
import os
import traceback
from pathlib import Path
from typing import Type, Any, Optional

# External python dependencies
from metakernel import MetaKernel, Magic
import logging
import yaml
from pydantic_ai import (
    Agent,
    ModelRequest,
    ModelMessage,
    SystemPromptPart,
    FunctionToolset,
    Tool,
    DeferredToolRequests,
    ToolDenied,
    DeferredToolResults,
)


def add_custom_logger_handler(
    logger: logging.Logger, log_dir="~/.pydantic_ai_kernel_logs/pydantic_ai.log"
):
    """
    Add a custom handlers to the metakernel logger; located
    in ~/.pydantic_ai_kernel_logs dir
    """
    log_dir = Path(log_dir).expanduser()
    fh = logging.FileHandler(log_dir, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)


class PydanticAIBaseKernel(MetaKernel):
    """
    Kernel wrapper for pydantic agents. Allows to interact with an AI agent
    through jupyter kernel messaging protocol.

    Allows to access agent history (tool calling history). Thanks to pydantic-ai
    library, nearly all inference providers are supported.
    With metakernel magics, you can load a new config file,
    display agent history.

    Tool validation is supported through pydantic-ai DeferredToolRequest
    being forwarded to frontend with jupyter input_request messages.

    Most of the metakernel magics are disabled on purpose.
    """

    implementation = "PydanticAI Base Agent Kernel"
    implementation_version = "1.0"
    language = "no-op"
    help_suffix = (
        "♫"  # unusual suffix on purpose, because ? is very common in natural language
    )
    language_version = "0.1"
    language_info = {
        "name": "pydantic_ai",
        "mimetype": "text/plain",
        "file_extension": ".ai",
    }
    banner = "Pydantic AI Base Kernel"

    def __init__(
        self,
        kernel_name: str = "pydantic_ai",
        agent_config: AgentConfig | None = None,
        tools: list[Tool] | None = None,
        toolsets: list[FunctionToolset] | None = None,
        output_type: Type = str,
        authorized_magics_names: list[str] | None = None,
        additional_agent_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ):
        """
        Parameters :
        ---
            - kernel_name (str = `pydantic_ai`) : the name of kernel. Used for fetching
                default config file. TODO : sync with metakernel name and default config
                files
            - agent_config (AgentConfig | None = None) : the configuration object for the
                agent. Deals with system prompt, inference provider API, ...
            - tools (list[Tool] | None = None) : list of pydantic-ai tools, which can be
                given to the agent on startup. Useful for subclasses.
            - toolsets (list[FunctionToolset] | None = None) : list of toolsets given to
                the agent on startup. Useful for subclasses.
            - output_type (Type = str) : python Type for a constrained output of the agent.
                See pydantic-ai documentation.
            - authorized_magics_names (list[str] | None = None) : Useful for subclasses.
                List of class names for the magics you want to whitelist for this kernel.
                By default, all non-whitelisted magics are not loaded. You must manually
                add a class name (e.g. FileMagic, ...) to have it running on this kernel.
            - additional_agent_kwargs (dict[str, Any] | None = None) : any kwargs which
                will be given to pydantic-ai agent initialization.
        """
        if authorized_magics_names is None:
            authorized_magics_names = []
        authorized_magics_names += [
            "HelpMagic",
            "MagicMagic",
            "LoadConfigMagic",
            "AgentHistoryMagic",
            "ToolMagic",
            "ForgetMagic",
        ]
        self.authorized_magics_names = authorized_magics_names
        self.additional_agent_kwargs = (
            additional_agent_kwargs if additional_agent_kwargs else {}
        )

        super().__init__(**kwargs)
        self.kernel_name = kernel_name
        if os.getenv("PYDANTIC_AI_KERNEL_LOG", False):
            add_custom_logger_handler(self.log)
        self.agent_config = agent_config

        self.tools = tools if tools is not None else []
        self.toolsets = toolsets
        self.output_type = output_type

        try:
            if self.agent_config is None:
                self.agent_config = self.load_config()

            self.agent = self.create_agent()
            self.message_history: list[ModelMessage] = [
                ModelRequest(
                    parts=[SystemPromptPart(content=self.agent_config.system_prompt)]
                )
            ]
        except Exception as e:
            self.log.debug(f"Could not load default config `{e}`")
            self.agent = None
        self.agent_history = []
        self.all_messages_ids = []
        self.user_validation = False
        self.log.info("Initialization of Pydantic AI Kernel is successful.")

    def reload_magics(self) -> None:
        """
        Override metakernel `reload_magics` to fix the magics not being
        propagated through subclasses. Subclasses of pydantic-ai-kernel
        could not by default access pydantic-ai-kernel.

        We first reload_magics with the official method, and then we seek
        for a magics dir **within** this file's directory.
        """
        super().reload_magics()
        try:
            this_class_magics_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "magics"
            )
            sys.path.append(this_class_magics_dir)
            this_class_magic_files = glob.glob(
                os.path.join(this_class_magics_dir, "*.py")
            )
            for this_class_magic in this_class_magic_files:
                basename = os.path.basename(this_class_magic)
                if basename == "__init__.py":
                    continue
                module = __import__(os.path.splitext(basename)[0])
                importlib.reload(module)
                module.register_magics(self)
        except Exception as e:
            self.log.debug(
                f"PydanticAIBaseKernel could not register its own magics : `{e}`."
            )

    def register_magics(self, magic_klass: type[Magic]) -> None:
        """
        Override the metakernel 'register_magics', to prevent of
        loading non-whitelisted magics.

        Parameters :
        ---
            - magic_klass: The subclass of Magic
        """
        if magic_klass.__name__ in self.authorized_magics_names:
            self.log.info(f"Adding magic : {magic_klass}")
            super().register_magics(magic_klass)

    def load_config(self, path: str | None = None) -> AgentConfig:
        """
        Try to load config file at ~/.jupyter/jupyter_<kernel_name>_config.yaml.
        Returns the validated config object, or raise an Error.

        Parameters :
        ---
            - path (Optional[str]) : path to the config file. If None,
                is set to ~/.jupyter/jupyter_<kernel_name>_config.yaml

        Returns :
        ---
            AgentConfig pydantic BaseModel, validated
        """
        if path is None:
            home = Path.home()
            dir = home / f".jupyter/jupyter_{self.kernel_name}_config.yaml"
        else:
            dir = path
        try:
            with open(dir, "rt") as f:
                conf = yaml.safe_load(f)
            validated_conf = AgentConfig.model_validate(conf)
            return validated_conf
        except Exception as e:
            raise Exception(
                f"Could not load and validate config file for agent at {dir}."
            ) from e

    def create_agent(self) -> Agent[None, Any]:
        """
        Creates the pydantic-ai agent, from config file.
        """
        if self.agent_config is None:
            raise ValueError("Could not create agent without configuration file.")
        try:
            model = self.agent_config.model.get_model
        except NotImplementedError as e:
            model = self.agent_config.model.model_name
            self.log.warning(e)
        agent = Agent(
            model,
            output_type=[self.output_type, DeferredToolRequests],
            system_prompt=self.agent_config.system_prompt,
            tools=self.tools,
            toolsets=self.toolsets,
            name=self.agent_config.agent_name,
            **self.additional_agent_kwargs,
        )

        return agent

    async def run_agent(
        self,
        prompt: Optional[str],
        deferred_tool_result: Optional[DeferredToolResults] = None,
    ) -> Optional[DeferredToolRequests]:
        """
        Runs the agent. Streams the output to stdout. Returns a DeferredToolRequest
        to ask for user approval if some tool needs it.
        Else, returns None.

        Can be called several times in the same question if the user gives
        its validation for tool calling.

        Parameters :
        ---
            - prompt (Optional[str]): the prompt given to the agent
            - deferred_tool_result (Optional[DeferredToolResults]) : optional
                tool approval / disapproval of the last agent run.

        Returns :
        ---
            None if all text output was streamed to stdout. A DeferredToolRequests
            object if the user needs to validate some tool calling.
        """
        if self.agent is None:
            raise Exception(
                r"Load config file before using the agent. Send `%load_config <config_dir>`. See https://github.com/mariusgarenaux/pydantic-ai-kernel to get config scheme."
            )
        last_text = ""
        tool_req = None
        async with self.agent.run_stream(
            prompt,
            message_history=self.agent_history,
            deferred_tool_results=deferred_tool_result,
        ) as response:
            async for out in response.stream_output():
                if isinstance(out, DeferredToolRequests):
                    tool_req = out
                    continue
                sendable_text = str(out).removeprefix(last_text)
                last_text += sendable_text
                self.Print(sendable_text, sep="", end="")

            all_msg = response.all_messages()
            self.log.debug(f"Adding : {all_msg} to agent history.")
            self.agent_history = all_msg
        return tool_req

    def ask_user_approval(self, prompt: Optional[str] = None) -> bool:
        """
        Sends a input_request message to the frontend, asking
        for user approval.

        Returns:
        ---
            True if the user gave his approval, else False
        """
        user_approval = self.raw_input(f"{prompt} ([y]/n):")
        return user_approval in ["Y", "yes", 1, "1", "y"]

    async def do_execute_direct(self, code: str, silent=False):
        """
        Sends the code to the agent, retrieve the output from
        an async loop, and stream it to IOPub channel.

        Parameters :
        ---
            - code (str): the code (prompt) which is sent to the agent
            - silent (bool = False) : whether to execute the code silently.
                See https://jupyter-client.readthedocs.io/en/stable/messaging.html#execute
        """
        try:
            if self.agent is None:
                raise Exception(
                    r"Load config file before using the agent. Send `%load_config <config_dir>`. See https://github.com/mariusgarenaux/pydantic-ai-kernel to get config scheme."
                )

            deferred_tool_result = None
            while True:
                # runs the agent until it returns anything other than a deferred
                # tool request.
                # if it outputs a deferred tool request, ask for user approval,
                # and then re-run the agent.
                prompt = code if deferred_tool_result is None else None
                agent_out = await self.run_agent(
                    prompt, deferred_tool_result=deferred_tool_result
                )
                self.log.info(f"Agent out : {agent_out}")
                # self.log.info(f"Agent history : {self.agent.history_processors}")

                if isinstance(agent_out, DeferredToolRequests):
                    results = DeferredToolResults()
                    for call in agent_out.approvals:
                        self.log.info(f"Call : {call}")
                        user_approved = self.ask_user_approval(
                            prompt_user_approval(call)
                        )
                        if not user_approved:
                            result = ToolDenied()
                        else:
                            result = True
                        results.approvals[call.tool_call_id] = result
                    deferred_tool_result = results
                else:
                    break

        except Exception:
            self.Error_display(traceback.format_exc())

    async def do_is_complete(self, code: str) -> dict[str, str]:
        """
         Overwrites metakernel do_is_complete to have :
             - magic commands requires an empty line (as usual)
             - non-magic commands do not need an empty line
             - non-magic commands can be multiline if the line
                 ends with ' '.
        u"""
        if code.startswith(self.magic_prefixes["magic"]):
            ## force requirement to end with an empty line
            if code.endswith("\n"):
                return {"status": "complete"}
            else:
                return {"status": "incomplete"}
        # otherwise, how to know is complete?
        elif code.endswith(" "):
            return {"status": "incomplete"}
        else:
            return {"status": "complete"}
