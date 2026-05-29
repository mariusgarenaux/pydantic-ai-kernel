from pydantic_ai_kernel import (
    PydanticAIBaseKernel,
    BoostedMagic,
    boosted_option,
    complete_from_list,
)
import ipywidgets as widgets
from pydantic_ai_kernel.utils import put_text_in_box
from pydantic_ai import Tool, FunctionToolset, ApprovalRequiredToolset
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

out_formatter_list = ["text", "terminal", "md"]


class ToolsMagic(BoostedMagic):
    @boosted_option(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Display verbose output",
    )
    @boosted_option(
        "-f",
        "--formatter",
        default=None,
        help="Formatter for the output. Must be supported by jupyter frontend. All formatter can be set by environment variable PYDANTIC_AI_KERNEL_FORMATTER",
        choices=out_formatter_list,
        completer=lambda w, r: complete_from_list(out_formatter_list, w, r),
    )
    def line_tools(self, verbose: bool = False, formatter: str | None = None):
        """
        %tools : tools of the agent

        Examples :
        -------
            • %tools -v : list tools, with verbose output
            • %tools --f=markdown : list of tools, mardown formatted
        """
        # Use kernel's configured formatter if not overridden
        env_formatter = getattr(self.kernel, "formatter", "text")
        if formatter is None:
            formatter = env_formatter
        self.kernel: PydanticAIBaseKernel  # type hints
        match formatter:
            case "text" | "terminal":
                self.text_format

                ter(verbose)
            case "md":
                if self.kernel.use_widget:
                    self.markdown_formatter_with_widget(verbose)
                else:
                    self.markdown_formatter(verbose)
            case _:
                raise NotImplementedError(
                    f"Unknown formatter : {formatter}. Accepted are : {out_formatter_list}"
                )

    def markdown_formatter_with_widget(self, verbose):
        """
        Display all tools in markdown
        """
        for each_tool in self.kernel.tools:
            if verbose:
                content = f"```python  \n{each_tool}```  \n"
            else:
                content = nice_tool_displaying(each_tool, formatter="md")

            self.kernel.Display(
                widgets.Accordion(
                    children=[
                        widgets.HTML(
                            value=content,
                            placeholder="",
                            description="",
                        )
                    ],
                    titles=[each_tool.name],
                )
            )
        if self.kernel.toolsets is not None:
            for each_toolset in self.kernel.toolsets:
                title = "toolset"
                if isinstance(each_toolset, ApprovalRequiredToolset):
                    each_toolset = each_toolset.wrapped
                content = ""
                if isinstance(each_toolset, FunctionToolset):
                    for each_tool in each_toolset.tools.values():
                        content += f"{each_tool.name}  \n"
                        if verbose:
                            content += f"{each_tool}  \n"
                        else:
                            content += nice_tool_displaying(each_tool, formatter="md")
                elif isinstance(each_toolset, FastMCPToolset):
                    content += f"- FastMCP : {each_toolset.client.transport.url}"
                else:
                    content += f"- {each_toolset}"
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

    def markdown_formatter(self, verbose):
        """
        Display all tools in markdown
        """
        out = ""
        for each_tool in self.kernel.tools:
            out += f"### {each_tool.name}  \n"
            if verbose:
                out += f"```python  \n{each_tool}```  \n"
            else:
                out += nice_tool_displaying(each_tool, formatter="md")
        if self.kernel.toolsets is not None:
            for each_toolset in self.kernel.toolsets:
                out += "\n### toolset  \n"
                if isinstance(each_toolset, ApprovalRequiredToolset):
                    each_toolset = each_toolset.wrapped
                if isinstance(each_toolset, FunctionToolset):
                    for each_tool in each_toolset.tools.values():
                        out += f"#### {each_tool.name}  \n"
                        if verbose:
                            out += f"{each_tool}  \n"
                        else:
                            out += nice_tool_displaying(each_tool, formatter="md")
                elif isinstance(each_toolset, FastMCPToolset):
                    out += f"- FastMCP : {each_toolset.client.transport.url}"
                else:
                    out += f"- {each_toolset}"
        self.kernel.Display(
            {"text/markdown": out},
        )

    def text_formatter(self, verbose):
        """
        Display all tools, in raw text output, ready for terminal.
        """
        for each_tool in self.kernel.tools:
            self.kernel.Print(each_tool.name)
            if verbose:
                self.kernel.Print(each_tool)
            else:
                self.kernel.Print(
                    put_text_in_box(nice_tool_displaying(each_tool), indent=2)
                )

        if self.kernel.toolsets is not None:
            for each_toolset in self.kernel.toolsets:
                self.kernel.Print("Toolset :")
                out = ""
                if isinstance(each_toolset, ApprovalRequiredToolset):
                    each_toolset = each_toolset.wrapped
                if isinstance(each_toolset, FunctionToolset):
                    for each_tool in each_toolset.tools.values():
                        out += each_tool.name + "\n"
                        if verbose:
                            out += f"{each_tool}"
                        else:
                            out += nice_tool_displaying(each_tool)
                elif isinstance(each_toolset, FastMCPToolset):
                    out += f"   FastMCP : {each_toolset.client.transport.url}"
                else:
                    out += f"  {each_toolset}"
                self.kernel.Print(put_text_in_box(out, indent=2))


def nice_tool_displaying(tool: Tool, formatter="text"):
    desc = tool.description if tool.description is not None else ""
    if formatter == "text":
        out = f"   description : {desc}\n"
        out += f"   requires approval : {tool.requires_approval}\n"
        return out
    elif formatter == "md":
        out = f"- description : {desc}  \n"
        out += f"- schema :  \n```json  \n{tool.function_schema.json_schema}  \n```  \n"
        out += f"- requires approval : {tool.requires_approval}  \n"
        return out
    return ""


def register_magics(kernel) -> None:
    kernel.register_magics(ToolsMagic)
