from pydantic_ai_kernel import PydanticAIBaseKernel
from metakernel import Magic


class ToolMagic(Magic):

    def line_tools(self):
        """
        %tools : tools of the agent
        """
        self.kernel: PydanticAIBaseKernel  # type hints
        self.kernel.Print(self.kernel.tools)


def register_magics(kernel) -> None:
    kernel.register_magics(ToolMagic)
