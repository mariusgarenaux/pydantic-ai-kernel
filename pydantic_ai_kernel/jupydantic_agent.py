from pydantic_ai import (
    Agent,
    DeferredToolResults,
    DeferredToolRequests,
    ModelRequestNode,
    PartStartEvent,
    PartDeltaEvent,
    ThinkingPart,
    TextPartDelta,
    TextPart,
    ThinkingPartDelta,
    PartEndEvent,
    ToolDenied,
    BinaryImage,
    ModelRequest,
    ToolReturnPart,
)
from metakernel import MetaKernel
from typing import Optional, Any
from pydantic import BaseModel, field_serializer, ConfigDict
import traceback

from .agent_config import AgentConfig
from .utils import prompt_user_approval

import ipywidgets as widgets


# Custom exception used to abort the agent's streaming loop when the kernel receives an interrupt.
class UserInterruptionError(Exception):
    """Raised internally to stop the async streaming of agent events."""

    pass


class SerializableWidget(BaseModel):
    """
    An Ipywidget, but serializable so that it can be
    produced by tools and agent output.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    widget: widgets.Widget

    @field_serializer("widget", mode="plain")
    def ser_widget(self, value: widgets.Widget) -> Any:
        return value.get_state()


class JuPydanticAgent:
    """
    Mixes a pydantic-ai agent and a jupyter kernel (through MetaKernel).
    Gives access to methods that allows the agent to be streamed to the kernel.
    Support different output types : markdown, html, widgets, raw text,
    colored text, images, ...

    This agent wrapper can be used with any MetaKernel instance; allowing
    to build complex multi agent applications.
    """

    def __init__(
        self, agent: Agent[None, Any], kernel: MetaKernel, agent_config: AgentConfig
    ):
        self.agent = agent
        self.agent_history = []
        self.agent_config = agent_config
        self.kernel = kernel
        self.log = self.kernel.log
        self.is_interrupted = False
        self.out_md_stack = []

    async def stream_agent_to_kernel(
        self,
        prompt: Optional[str],
        deferred_tool_results: Optional[DeferredToolResults] = None,
    ) -> DeferredToolRequests | Any:
        """
        Runs the agent once, and streams the output to stdout.
        Returns a DeferredToolRequest to ask for user approval if some tool needs it.
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
            object if the user needs to validate some tool calling. Can be the
            Agent output type.
        """
        agent_output = None

        async with self.agent.iter(
            user_prompt=prompt,
            message_history=self.agent_history,
            deferred_tool_results=deferred_tool_results,
        ) as agent_run:
            if self.is_interrupted:
                raise UserInterruptionError("User stopped the execution")
            async for node in agent_run:
                # The inner stream already aborts via UserInterruptionError,
                # but we keep the old guard as a fallback.
                if self.is_interrupted:
                    raise UserInterruptionError("User stopped the execution")

                # self.Print(f"node : {node}")
                if Agent.is_user_prompt_node(node):
                    continue
                elif Agent.is_model_request_node(node):
                    await self.deal_with_model_request_node(node, agent_run.ctx)
                elif Agent.is_call_tools_node(node):
                    self.log.debug(f"Calling tool node : {node}")
                elif Agent.is_end_node(node):
                    # either agent output or DeferredToolRequest
                    agent_output = node.data.output

            self.agent_history = agent_run.all_messages()

        self.last_usage = agent_run.usage

        return agent_output

    async def deal_with_model_request_node(
        self, model_request_node: ModelRequestNode, ctx
    ):
        if self.agent_config is None:
            self.log.warning("No config was found for agent during its request")
            return
        self.log.info(model_request_node.request)
        self.log.info(model_request_node._result)

        # all_parts = model_request_node.request.parts
        # for part in
        # if isinstance(.parts[0], ToolReturnPart):
        #     if isinstance(model_request_node.request.parts[0].content, Widget):
        #         self.Display(model_request_node.request.parts[0].content)
        #         model_request_node.request.parts[0].content = "Widget"
        #         return
        out_md = ""
        think_content = ""
        async with model_request_node.stream(ctx) as request_stream:
            async for event in request_stream:
                if self.is_interrupted:
                    raise UserInterruptionError("Interrupt received while streaming")
                if isinstance(event, PartStartEvent):
                    if (
                        isinstance(event.part, ThinkingPart)
                        and self.agent_config.display_thinking
                    ):
                        self.kernel.Print("========= Thinking =========")
                        self.kernel.Print(event.part.content, end="")

                        if self.use_widget:
                            think_content += event.part.content
                        else:
                            out_md += "> **Thinking** :  \n"
                            out_md += f"> {event.part.content}"

                    if isinstance(event.part, TextPart):
                        self.kernel.Print(event.part.content, end="")
                        out_md += event.part.content
                if isinstance(event, PartDeltaEvent):
                    if (
                        isinstance(event.delta, ThinkingPartDelta)
                        and event.delta.content_delta is not None
                        and self.agent_config.display_thinking
                    ):
                        self.kernel.Print(
                            event.delta.content_delta,
                            end="",
                        )
                        if self.use_widget:
                            think_content += event.delta.content_delta
                        else:
                            out_md += event.delta.content_delta.replace("\n", "  \n> ")

                    if isinstance(event.delta, TextPartDelta):
                        self.kernel.Print(event.delta.content_delta, end="")
                        out_md += event.delta.content_delta
                if isinstance(event, PartEndEvent):
                    if (
                        isinstance(event.part, ThinkingPart)
                        and self.agent_config.display_thinking
                    ):
                        self.kernel.Print("\n========= End Think =========")
                        out_md += "  \n  \n"

        if len(think_content) > 0 and self.use_widget:
            self.out_md_stack.append(
                widgets.Accordion(
                    children=[
                        widgets.HTML(
                            value=think_content,
                            placeholder="",
                            description="",
                        )
                    ],
                    titles=["Though"],
                )
            )
        if len(out_md) > 0:
            # avoid display empty blocks
            self.out_md_stack.append({"text/markdown": out_md})
        if self.formatter == "md":
            # this line could break things, because we bet
            # here that frontends that can't display markdown
            # are also those that can't clear output
            # (for ex. jupyter console).
            # since there is no way to know if a frontend
            # really clears output on clear_output msg, this
            # remains the best option
            # we could also have an environment variable to set
            # if the current frontend implements clear_output
            self.kernel.Display(
                *self.out_md_stack,
                clear_output=True,
            )

    @property
    def formatter(self):
        return self.agent_config.formatter

    @property
    def use_widget(self):
        return self.agent_config.use_widget

    async def run(self, prompt: str, silent: bool = False):
        """
        Makes several runs of the agent, until all tool calls
        are processed. Streams its output to the kernel. All
        the tool calls are dealt with input_message.
        """
        try:
            self.is_interrupted = False
            deferred_tool_result = None
            self.out_md_stack = []
            while True:
                # runs the agent until it returns anything other than a deferred
                # tool request.
                # if it outputs a deferred tool request, ask for user approval,
                # and then re-run the agent.
                prompt_or_tool_result = prompt if deferred_tool_result is None else None
                agent_out = await self.stream_agent_to_kernel(
                    prompt_or_tool_result, deferred_tool_results=deferred_tool_result
                )

                # self.log.info(f"Agent out : {agent_out}")
                # self.log.info(f"Agent history : {self.agent.history_processors}")
                # If an interrupt was received while the agent was running, stop the loop immediately.
                if self.is_interrupted:
                    self.log.info("Execution halted by user interrupt")
                    break

                if isinstance(agent_out, DeferredToolRequests):
                    results = DeferredToolResults()
                    for call in agent_out.approvals:
                        self.log.info(f"Call : {call}")

                        user_validation = self.kernel.raw_input(
                            f"{prompt_user_approval(call)} ([y]/n):"
                        )
                        if user_validation not in ["Y", "yes", 1, "1", "y"]:
                            result = ToolDenied(
                                f"User rejected the tool call : {user_validation}"
                            )
                        else:
                            result = True
                        results.approvals[call.tool_call_id] = result
                    deferred_tool_result = results
                elif isinstance(agent_out, str):
                    break
                elif isinstance(agent_out, BinaryImage):
                    self.kernel.Display({"image/png": agent_out.data})
                    break
                elif isinstance(agent_out, SerializableWidget):
                    self.kernel.Display(agent_out.widget)
                    break
                else:  # here, check for unprocessed tool calls, and remove them
                    last_msg = self.agent_history[-1]
                    # self.log.info(f"Last message : {last_msg}")
                    # self.log.info(f"Last message first part : {last_msg.parts[0]}")
                    # self.log.info(
                    #     f"Last message first part content : {last_msg.parts[0].content}"
                    # )
                    if (
                        isinstance(last_msg, ModelRequest)
                        and isinstance(last_msg.parts[0], ToolReturnPart)
                        and last_msg.parts[0].content
                        == "Tool not executed - a final result was already processed."
                    ):
                        self.agent_history.pop(-1)
                        self.agent_history.pop(-1)
                        self.log.info(
                            f"Popped last elem. Agent history now : {self.agent_history}"
                        )
                        # TODO : force for deferred tool in this case also (else some tool
                        # calls are skipped)
                    break

        except UserInterruptionError:
            self.log.info("User interrupted the loop")
        except Exception:
            self.kernel.Error_display(traceback.format_exc())
