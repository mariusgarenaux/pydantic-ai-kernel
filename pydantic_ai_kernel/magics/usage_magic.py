import os
import json
import dataclasses
from pydantic_ai_kernel import BoostedMagic, boosted_option, PydanticAIBaseKernel


class UsageMagic(BoostedMagic):
    @boosted_option(
        "-f",
        "--formatter",
        default=None,
        help="Formatter for the output (text, terminal, md, json).",
        choices=["text", "terminal", "md", "json"],
    )
    def line_usage(self, formatter: str | None = None) -> None:
        """
        %usage : display the most recent usage information from the last agent run.

        If no usage data is available, a helpful message is shown.
        """
        self.kernel: PydanticAIBaseKernel  # type hint for kernel
        # Determine formatter, default to environment variable or text

        # Use kernel's configured formatter if not overridden
        env_formatter = getattr(self.kernel, "formatter", "text")
        if formatter is None:
            formatter = env_formatter

        usage_info = self.kernel.agent.last_usage
        if usage_info is None:
            self.kernel.Error(
                "No usage information available. Run a cell to generate usage data."
            )
            return

        # Nice formatting based on requested type
        # Convert usage info to a dict (handles RunUsage dataclass)
        info_dict = (
            usage_info
            if isinstance(usage_info, dict)
            else dataclasses.asdict(usage_info)
        )
        if formatter == "json":
            try:
                json_str = json.dumps(info_dict, indent=2)
            except Exception:
                json_str = str(info_dict)
            self.kernel.Print(json_str)
        elif formatter == "md":
            # Render as a markdown table
            rows = ["| Key | Value |", "| --- | ----- |"]
            for k, v in info_dict.items():
                rows.append(f"| {k} | {v} |")
            md_content = "\n".join(rows)
            self.kernel.Display({"text/markdown": md_content})
        else:
            # text or terminal – formatted key: value lines
            lines = [f"{k}: {v}" for k, v in info_dict.items()]
            self.kernel.Print("\n".join(lines))


def register_magics(kernel) -> None:
    kernel.register_magics(UsageMagic)
