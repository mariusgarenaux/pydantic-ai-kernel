import os
from pydantic_ai_kernel import PydanticAIBaseKernel
from metakernel import Magic, option


class LoadConfigMagic(Magic):
    @option(
        "-r",
        "--reset",
        action="store_true",
        default=False,
        help="Whether to reset agent history or not",
    )
    def line_load_config(self, path, reset: bool) -> None:
        """
        %load_config PATH : loads the agent config

        Loads the agent configuration located at path
        """
        self.kernel: PydanticAIBaseKernel  # type hints
        self.evaluate = False

        path = os.path.expanduser(path)
        self.kernel

        self.kernel.agent_config = self.kernel.load_config(path=path)
        agent = self.kernel.create_agent()
        self.kernel.agent = agent
        if reset:
            self.message_history = []

        self.kernel.Print(f"Updated config file from {path}")


def register_magics(kernel) -> None:
    kernel.register_magics(LoadConfigMagic)
