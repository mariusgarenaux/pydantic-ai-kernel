from pydantic_ai_kernel import PydanticAIBaseKernel
from metakernel import Magic


class ForgetMagic(Magic):
    def line_forget(self):
        """
        %forget : empty the agent history.
        """
        self.kernel: PydanticAIBaseKernel
        self.kernel.agent.agent_history = []
        self.kernel.Print("Removed the agent memory.")


def register_magics(kernel) -> None:
    kernel.register_magics(ForgetMagic)
