from pydantic_ai_kernel import BoostedMagic, PydanticAIBaseKernel


class FormatterMagic(BoostedMagic):
    def line_formatter(self, fmt: str) -> None:
        """%formatter <fmt>: change the kernel output formatter.

        Accepted values are ``text``, ``terminal``, ``md`` and ``json``.
        The selected formatter is stored in ``kernel.formatter`` and will be used
        by other magics that rely on the environment variable fallback.
        """
        self.kernel: PydanticAIBaseKernel  # type hint
        allowed = ["text", "terminal", "md", "json"]
        if fmt not in allowed:
            self.kernel.Error(f"Invalid formatter '{fmt}'. Allowed: {allowed}")
            return
        self.kernel.formatter = fmt
        self.kernel.Print(f"Formatter set to {fmt}.")


def register_magics(kernel) -> None:
    kernel.register_magics(FormatterMagic)
