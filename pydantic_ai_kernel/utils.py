import textwrap
from pydantic_ai import ToolCallPart
import json
from typing import Optional


def nice_display_tool_args(tool_args: Optional[str | dict]) -> str:
    """
    Format arguments of a tool call in a pretty string.
    Deals with multiline arguments.
    """
    args_str = ""
    if tool_args is None:
        return args_str

    args = None
    if isinstance(tool_args, str):
        try:
            args = json.loads(tool_args)
        except Exception:
            args_str = tool_args

    if isinstance(args, dict):
        for key, value in args.items():
            args_str += f"• {key} :\n{textwrap.indent(text=str(value), prefix='   ', predicate=lambda line: True)}\n"

    args_str = args_str.removesuffix("\n")
    return args_str


def prompt_user_approval(tool_call: ToolCallPart) -> str:
    """
    Nice display of user-approval request.
    Takes into account multiline argument (for long string
    as argument of tools - e.g. code).
    """
    out = "\nApprove the call of tool :\n"
    out += f"   {tool_call.tool_name}\n"
    args_str = nice_display_tool_args(tool_call.args)
    out += put_text_in_box(args_str, indent=4)
    return out


def put_text_in_box(text: str, indent: int) -> str:
    """
    Creates a string where the text is in a box,
    with an indentation of indent. Deals with
    multi-line text.

    Example : (text = 'Hey !', indent=4)
    ---
            │   Hey !
            ╰───────────────────────────────

    Parameters :
    ---
        - text (str) : the text inside the box
        - indent (int) : the indent of the box

    Returns :
    ---
        A string that represents the string, in a
        pretty box.
    """
    out = ""
    preshift = " " * indent + "│" + " " * 3

    out += f"{textwrap.indent(text, preshift, predicate=lambda line: True)}\n"
    out += " " * indent + "╰─" + "─" * 30 + "\n"
    return out


class MCPToolsetError(Exception):
    pass


class LoadConfigError(Exception):
    pass
