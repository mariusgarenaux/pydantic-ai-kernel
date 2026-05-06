from pydantic_ai_kernel import PydanticAIBaseKernel, BoostedMagic, boosted_option
from pydantic_ai_kernel.utils import put_text_in_box
from pydantic_ai import Tool, FunctionToolset, ToolsetFunc, ApprovalRequiredToolset
from pydantic_ai.toolsets.fastmcp import FastMCPToolset


class ToolMagic(BoostedMagic):
    @boosted_option(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Display verbose output",
    )
    def line_tools(self, verbose: bool = False):
        """
        %tools : tools of the agent

        Examples :
        -------
            • %tools -v : list tools, with verbose output
        """
        self.kernel: PydanticAIBaseKernel  # type hints
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


def nice_tool_displaying(tool: Tool):
    desc = tool.description if tool.description is not None else ""
    out = f"   description : {desc}\n"
    out += f"   requires approval : {tool.requires_approval}\n"
    return out


def register_magics(kernel) -> None:
    kernel.register_magics(ToolMagic)
