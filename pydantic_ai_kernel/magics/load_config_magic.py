import os
from pydantic_ai_kernel import PydanticAIBaseKernel
from metakernel import Magic


class LoadConfigMagic(Magic):

    def line_load_config(self, path) -> None:
        """
        %load_config - loads the agent config

        Loads the agent configuration located at path
        """
        self.kernel: PydanticAIBaseKernel  # type hints
        self.evaluate = False

        path = os.path.expanduser(path)
        self.kernel

        self.kernel.agent_config = self.kernel.load_config(path=path)
        agent = self.kernel.create_agent()
        self.kernel.agent = agent
        self.message_history = []

        self.kernel.Print(f"Updated config file from {path}")


def register_magics(kernel) -> None:
    kernel.register_magics(LoadConfigMagic)
