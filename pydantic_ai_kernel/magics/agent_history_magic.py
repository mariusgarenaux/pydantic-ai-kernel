from pydantic_ai_kernel import (
    PydanticAIBaseKernel,
    BoostedMagic,
    boosted_option,
    complete_from_list,
)
import ipywidgets as widgets
from pydantic_ai_kernel.utils import put_text_in_box, nice_display_tool_args
from typing import Tuple
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequestPart,
    SystemPromptPart,
    UserPromptPart,
    ToolReturnPart,
    RetryPromptPart,
    ModelResponsePart,
    TextPart,
    ToolCallPart,
    NativeToolCallPart,
    ModelMessagesTypeAdapter,
    ThinkingPart,
    FilePart,
)

out_formatter_list = ["text", "terminal", "md", "json"]


class AgentHistoryMagic(BoostedMagic):

    @boosted_option(
        "-f",
        "--formatter",
        default=None,
        help="Formatter for the output. Must be supported by jupyter frontend. All formatter can be set by environment variable PYDANTIC_AI_KERNEL_FORMATTER",
        choices=out_formatter_list,
        completer=lambda w, r: complete_from_list(out_formatter_list, w, r),
    )
    def line_agent_history(self, formatter: str | None = None) -> None:
        """
        %agent_history : displays the agent history

        Examples :
        -------
            • `%agent_history --formatter md` : markdown display of agent history

        """
        # Use kernel's configured formatter if not overridden
        env_formatter = getattr(self.kernel, "formatter", "text")
        if formatter is None:
            formatter = env_formatter
        self.kernel: PydanticAIBaseKernel
        self.evaluate = False
        history: list[ModelMessage] = self.kernel.agent_history

        structured_messages = structured_message_display(history)

        if formatter == "json":
            self.kernel.Print(
                ModelMessagesTypeAdapter.dump_json(history, indent=4).decode("utf-8")
            )
            return

        for title, content in structured_messages:
            if formatter == "md":
                if self.kernel.use_widget:
                    self.kernel.Display(
                        widgets.Accordion(
                            children=[
                                widgets.HTML(
                                    value=content,
                                    placeholder="",
                                    description="",
                                )
                            ],
                            titles=[title],
                        )
                    )
                else:
                    self.kernel.Display({"text/markdown": f"### {title}  \n{content}"})
            elif formatter == "text":
                self.kernel.Print(f"  {title} :\n" + put_text_in_box(content, 4))
            elif formatter == "terminal":
                self.kernel.Print(
                    f"  \033[0;32m{title}\033[0m :\n" + put_text_in_box(content, 4)
                )


def get_title_content_from_message_part(
    part: ModelRequestPart | ModelResponsePart,
) -> Tuple[str, str]:
    """
    Transform the model message part in a string that is more human-readable.

    Parameters :
    ---
        - part (ModelRequestPart | ModelResponsePart) : the pydantic-ai object
            containing the information
        - indent (int) : the number of empty spaces before the text is displayed
        - formatter (str) : the formatter, can be md (markdown), text (raw text), terminal (
            raw text with ANSI colors).

    Returns :
    ---
        - a string, which should be printed.
    """
    title = ""
    content = ""
    if isinstance(part, SystemPromptPart):
        title = "System Prompt"
        content = part.content
    elif isinstance(part, UserPromptPart):
        title = "User Prompt"
        content = str(part.content)
    elif isinstance(part, ToolReturnPart):
        title = "Tool Return"
        content = f"{part.tool_name} : {part.content}"
    elif isinstance(part, RetryPromptPart):
        title = "Retry"
        content = str(part.content)
    elif isinstance(part, TextPart):
        title = "Text"
        content = part.content
    elif isinstance(part, ToolCallPart) or isinstance(part, NativeToolCallPart):
        title = "Tool Calling"
        content = (
            f"Name : `{part.tool_name}`\nArgs :\n{nice_display_tool_args(part.args)}"
        )
    elif isinstance(part, ThinkingPart):
        title = "Thinking"
        content = part.content
    elif isinstance(part, FilePart):
        title = "File"

    return title, content


def structured_message_display(history: list[ModelMessage]) -> list[Tuple[str, str]]:
    """
    Structure all the messages, ready to be displayed according to formatter

    Parameters:
    ---
        - history (list[ModelMessage]): the list of model message
    """
    out = []
    for each_model_message in history:
        for each_part in each_model_message.parts:
            title, content = get_title_content_from_message_part(each_part)
            out.append((title, content))
    return out


def register_magics(kernel) -> None:
    kernel.register_magics(AgentHistoryMagic)
