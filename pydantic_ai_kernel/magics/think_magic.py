from pydantic_ai_kernel import BoostedMagic, PydanticAIBaseKernel


class ThinkMagic(BoostedMagic):
    def line_think(self) -> None:
        """Toggle the display of the agent's thinking text.

        Each call flips the current ``display_thinking`` flag in the in‑memory
        configuration and prints the new state (``on`` or ``off``).
        """
        self.kernel: PydanticAIBaseKernel  # type hint

        # Ensure a configuration object exists
        if self.kernel.agent_config is None:
            # Load the default configuration if none is loaded yet
            self.kernel.agent_config = self.kernel.load_config()

        # Toggle the flag
        current = self.kernel.agent_config.display_thinking
        self.kernel.agent_config.display_thinking = not current
        new_state = "on" if self.kernel.agent_config.display_thinking else "off"
        self.kernel.Print(f"display_thinking set to {new_state}.")


def register_magics(kernel) -> None:
    kernel.register_magics(ThinkMagic)
