from pydantic_ai_kernel import (
    PydanticAIBaseKernel,
    BoostedMagic,
    boosted_option,
    complete_from_list,
)
import os
from pydantic_ai_kernel.utils import put_text_in_box, nice_display_tool_args

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
        env_formatter = os.getenv("PYDANTIC_AI_KERNEL_FORMATTER", "text")
        if formatter is None:
            formatter = env_formatter
        self.kernel: PydanticAIBaseKernel
        self.evaluate = False
        history: list[ModelMessage] = self.kernel.agent_history

        match formatter:
            case "json":
                self.kernel.Print(
                    ModelMessagesTypeAdapter.dump_json(history, indent=4).decode(
                        "utf-8"
                    )
                )
            case "md":
                out = ""
                for each_model_message in history:
                    out += nice_model_message_display(each_model_message, formatter)
                self.kernel.Display({"text/markdown": out})
            case "text" | "terminal":
                out = ""
                for each_model_message in history:
                    out += nice_model_message_display(each_model_message, formatter)
                self.kernel.Print(out)


def nice_display_model_message_part(
    part: ModelRequestPart | ModelResponsePart, indent: int, formatter: str
) -> str:
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

    match formatter:
        case "text":
            title = title
        case "terminal":
            title = f"\033[0;32m{title}\033[0m"
        case "md":
            title = f"### {title}  \n"

    match formatter:
        case "text" | "terminal":
            out = " " * 2 + title + " :\n"
            out += put_text_in_box(content, indent)
        case "md":
            out = title
            out += f"{content}  \n"
        case _:
            out = ""
    return out


def nice_model_message_display(message: ModelMessage, formatter: str) -> str:
    """
    Display all the parts of the message, in a box with the part type as a box title.

    Parameters:
    ---
        - message (ModelMessage) : a pydantic-ai ModelMessage, containing text / tool call
            informations
        - formatter (str) : the formatter, can be md (markdown), text (raw text), terminal (
            raw text with ANSI colors).

    Returns :
    ---
        A string which should be printed, containing the message history.
    """
    indent = 4
    out = ""
    for each_part in message.parts:
        out += nice_display_model_message_part(each_part, indent, formatter)
    return out


def register_magics(kernel) -> None:
    kernel.register_magics(AgentHistoryMagic)
