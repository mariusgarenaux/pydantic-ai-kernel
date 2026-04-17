# Internal Imports
from .agent_config import AgentConfig
from .utils import prompt_user_approval

# Base python dependencies
import importlib
import glob
import sys
import os
import traceback
import asyncio
from pathlib import Path
from typing import Type, Any, Optional, AsyncIterable

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
    AgentStreamEvent,
    RunContext,
)


def add_custom_logger_handler(logger: logging.Logger):
    """
    Add a custom handlers to the metakernel logger; located
    in ~/.jupyter/logs dir
    """
    log_file = os.getenv(
        "PYDANTIC_AI_KERNEL_LOG_FILE",
        Path("~/.jupyter/logs/pydantic_ai.log").expanduser(),
    )
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    log_level = os.getenv("PYDANTIC_AI_KERNEL_LOG_LEVEL", "INFO")
    logger.setLevel(log_level)


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
    app_name = "pydantic_ai"

    def __init__(
        self,
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
            "EditConfigMagic",
            "WriteConfigMagic",
        ]
        self.authorized_magics_names = authorized_magics_names
        self.additional_agent_kwargs = (
            additional_agent_kwargs if additional_agent_kwargs else {}
        )

        super().__init__(**kwargs)
        if os.getenv("PYDANTIC_AI_KERNEL_LOG_LEVEL", False):
            add_custom_logger_handler(self.log)
        self.agent_config = agent_config

        self.tools = tools if tools is not None else []
        self.toolsets = toolsets
        self.output_type = output_type
        self.is_interrupted = False  # boolean that is triggered by an interrupt_message
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
        self.config_has_changed = False
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

    def get_config_dir(self) -> str:
        home_directory = os.path.expanduser("~")
        config_name = f"jupyter_{self.app_name}_config.yaml"
        return os.path.join(home_directory, f".jupyter/{config_name}")

    def load_config(self, path: str | None = None) -> AgentConfig:
        """
        Try to load config file at ~/.jupyter/jupyter_<kernel_name>_config.yaml.
        Returns the validated config object, or raise an Error.

        Parameters :
        ---
            - path (Optional[str]) : path to the config file. If None,
                is set to ~/.jupyter/jupyter_<app_name>_config.yaml

        Returns :
        ---
            AgentConfig pydantic BaseModel, validated
        """
        if path is None:
            dir = self.get_config_dir()
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
        Creates the pydantic-ai agent, from config file. Can be overriden
        by a sub-class to implement any pydantic-ai agent.
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

    async def handle_event(self, event: AgentStreamEvent):
        if isinstance(event, DeferredToolRequests):
            return

    async def event_stream_handler(
        self,
        ctx: RunContext,
        event_stream: AsyncIterable[AgentStreamEvent],
    ):
        async for event in event_stream:
            await self.handle_event(event)

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
            event_stream_handler=self.event_stream_handler,
        ) as response:
            async for out in response.stream_output():
                if self.is_interrupted:
                    # https://github.com/pydantic/pydantic-ai/issues/1524
                    # TODO : wait pydantic-ai implements clean close
                    # of stream loop
                    # for the moment, a warning is displayed
                    raise UserInterruptionError("Execution stopped by user")

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
            if self.config_has_changed:
                self.agent_config = self.load_config()
                self.agent = self.create_agent()
                self.config_has_changed = False

            if self.agent is None:
                raise Exception(
                    r"Load config file before using the agent. Send `%load_config <config_dir>`. See https://github.com/mariusgarenaux/pydantic-ai-kernel to get config scheme."
                )
            self.is_interrupted = False
            deferred_tool_result = None
            while True:
                # runs the agent until it returns anything other than a deferred
                # tool request.
                # if it outputs a deferred tool request, ask for user approval,
                # and then re-run the agent.
                prompt = code if deferred_tool_result is None else None
                agent_out = asyncio.create_task(
                    self.run_agent(prompt, deferred_tool_result=deferred_tool_result)
                )
                await agent_out
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

    async def interrupt_request(self, stream, ident, parent):
        """
        This method is called when an interrupt_request message is received.

        By default, Ipykernel restart the kernel on an interrupt request.
        We override this here, to make an early stop of the agent stream.
        """
        self.log.info("Cell interuption asked ")
        if not self.session:
            return

        self.is_interrupted = True
        content = {"status": "ok"}
        self.session.send(stream, "interrupt_reply", content, parent, ident=ident)
        return


class UserInterruptionError(Exception):
    pass
