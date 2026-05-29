from pydantic_ai_kernel import PydanticAIBaseKernel, BoostedMagic, boosted_option
from pydantic_ai_kernel.utils import MCPToolsetError
from pydantic_ai.mcp import load_mcp_toolsets
from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from pydantic_ai import ApprovalRequiredToolset


class FastMCPMagic(BoostedMagic):
    @boosted_option(
        "--url",
        "-u",
        default=None,
        help="In case of streamable-http or sse transport, the url of the MCP server. For stdio transport, the name of the script (e.g. `my_server.py`)",
    )
    @boosted_option(
        "--config", "-c", help="The path towards a JSON MCP Configuration file."
    )
    @boosted_option(
        "--no-approval",
        default=False,
        action="store_true",
        help="If set, the MCP server will not need user approval for tool execution",
    )
    def line_fastmcp(
        self,
        url: str | None = None,
        config: str | None = None,
        no_approval: bool = False,
    ):
        """
        %fastmcp --url <mcp_server_url | local file path> : add an MCP server to agent tools

        Examples :
        -------
            • %fastmcp --url http://127.0.0.1:8000/mcp
        """
        self.kernel.log.warning(
            "%fastmcp magic is deprecated, from pydantic-ai. Use %mcp magic instead."
        )
        if url is not None:
            mcp_toolset = FastMCPToolset(url)
            to_display = f"located at : {url}"
        else:
            if config is None:
                raise MCPToolsetError(
                    "You must specify either an URL for http or sse connection, or --stdio_command and --stdio_args parameters for stdio connection."
                )
            mcp_toolset = FastMCPToolset(config)
            to_display = f"with config : {config}"
        self.kernel.log.info(f"Successfully connected to MCP server, {to_display}")
        self.kernel.Print(f"Successfully connected to MCP server, {to_display}")
        self.kernel: PydanticAIBaseKernel
        if self.kernel.toolsets is None:
            self.kernel.toolsets = [mcp_toolset]
        else:
            if no_approval:
                toolset = mcp_toolset
            else:
                toolset = ApprovalRequiredToolset(
                    mcp_toolset
                )  # by default, MCP requires
            # approval for all calls
            self.kernel.toolsets.append(toolset)

        # reset agent
        self.kernel._agent = self.kernel.create_agent()
        self.kernel.Print("Added MCP server as tool of the agent.")


def register_magics(kernel) -> None:
    kernel.register_magics(FastMCPMagic)
