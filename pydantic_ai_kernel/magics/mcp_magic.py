from pydantic_ai_kernel import PydanticAIBaseKernel, BoostedMagic, boosted_option
from pydantic_ai_kernel.utils import MCPToolsetError
from pydantic_ai.mcp import MCPServerStreamableHTTP, MCPServerSSE, MCPServerStdio


def create_mcp_toolset(
    transport, **kwargs
) -> MCPServerSSE | MCPServerStreamableHTTP | MCPServerStdio:
    match transport:
        case "sse":
            url = kwargs["url"]
            return MCPServerSSE(url)
        case "streamable-http":
            url = kwargs["url"]
            return MCPServerStreamableHTTP(url)
        case "http":
            raise DeprecationWarning(
                "Transport mode `http` is deprecated. Use `sse` instead."
            )
        case "stdio":
            stdio_command = kwargs["stdio_command"]
            stdio_args = kwargs["stdio_args"]
            return MCPServerStdio(stdio_command, stdio_args)
        case _:
            raise ValueError(
                f"Unexpected value for transport of MCP server : `{transport}`"
            )


class MCPMagic(BoostedMagic):
    @boosted_option(
        "--url",
        "-u",
        default=None,
        help="In case of streamable-http or sse transport, the url of the MCP server.",
    )
    @boosted_option(
        "--stdio_cmd",
        default=None,
        help="In case of stdio transport, the command of stdio server (ex: `python`)",
    )
    @boosted_option(
        "--stdio_args",
        default=None,
        help="In case of stdio transport, the args of the server (ex: `['mcp_server.py']`). Must be a list of str.",
    )
    @boosted_option(
        "--sse",
        action="store_true",
        default=False,
        help="Whether to use HTTP server with sse.",
    )
    def line_mcp(
        self,
        url: str | None = None,
        stdio_cmd: str | None = None,
        stdio_args: list[str] | None = None,
        sse: bool = False,
    ):
        """
        %mcp : adds an MCP server to tools of the agent

        Examples :
        -------
            • %mcp --url http://127.0.0.1:8000/mcp : connects
                to server with streamable-http
            • %mcp --stdio_cmd python --stdio_args ['my_mcp.py'] :
                connects to MCP server through stdin / stdout
            • %mcp --url http://127.0.0.1:8000/sse : connects
                to server with sse
        """
        if url is not None:
            if sse:
                mcp_toolset = create_mcp_toolset("sse", url=url)
            else:
                mcp_toolset = create_mcp_toolset("streamable-http", url=url)
            to_display = f"located at : {url}"
        else:
            if stdio_cmd is None and stdio_args is None:
                raise MCPToolsetError(
                    "You must specify either an URL for http or sse connection, or --stdio_command and --stdio_args parameters for stdio connection."
                )
            mcp_toolset = create_mcp_toolset(
                "stdio", stdio_command=stdio_cmd, stdio_args=stdio_args
            )
            to_display = f"with stdio : {stdio_cmd}, {stdio_args}"
        self.kernel.log.info(f"Successfully connected to MCP server, {to_display}")
        self.kernel.Print(f"Successfully connected to MCP server, {to_display}")
        self.kernel: PydanticAIBaseKernel
        if self.kernel.toolsets is None:
            self.kernel.toolsets = [mcp_toolset]
        else:
            self.kernel.toolsets.append(mcp_toolset)

        # reset agent
        self.kernel.agent = self.kernel.create_agent()
        self.kernel.Print("Added MCP server as tool of the agent.")


def register_magics(kernel) -> None:
    kernel.register_magics(MCPMagic)
