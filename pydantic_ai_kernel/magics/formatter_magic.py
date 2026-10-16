from pydantic_ai_kernel import PydanticAIBaseKernel
from boosted_magics import BoostedMagic, boosted_option
from boosted_magics.boosted_magic import complete_from_list


class FormatterMagic(BoostedMagic):

    @boosted_option(
        "format",
        completer=lambda w, r: complete_from_list(
            ["text", "terminal", "md", "json"], w, r
        ),
    )
    def line_formatter(self, format: str) -> None:
        """%formatter <fmt>: change the kernel output formatter.

        Accepted values are ``text``, ``terminal``, ``md`` and ``json``.
        The selected formatter is stored in ``kernel.formatter`` and will be used
        by other magics that rely on the environment variable fallback.
        """
        self.kernel: PydanticAIBaseKernel  # type hint
        allowed = ["text", "terminal", "md", "json"]
        if format not in allowed:
            self.kernel.Error(f"Invalid formatter '{format}'. Allowed: {allowed}")
            return
        if self.kernel.agent_config is None:
            self.kernel.Print("No agent configuration was found. Can't set formatter")
            return
        self.kernel.agent_config.formatter = format
        self.kernel.Print(f"Formatter set to {format}.")


def register_magics(kernel) -> None:
    kernel.register_magics(FormatterMagic)
